import asyncio
import inspect
from typing import Any, Optional
from datetime import datetime

from ms1_vision.domain.ports.diagnostic_ports import VisionClientPort, DiagnosticRepositoryPort
from ms1_vision.domain.schemas import DiagnosticModel, VisionOutputModel
import logging


class CreateDiagnosticUseCase:
    def __init__(
        self,
        vision_client: VisionClientPort,
        diagnostic_repo: DiagnosticRepositoryPort,
        django_patch_client: Any,
        redis_publisher: Any,
    ) -> None:
        self.vision_client = vision_client
        self.diagnostic_repo = diagnostic_repo
        self.django_patch_client = django_patch_client
        self.redis_publisher = redis_publisher

    async def execute(self, image_bytes: bytes, plant_id: str, token: str) -> DiagnosticModel:
        # 1. Run vision inference (support sync or async analyze)
        analyze = getattr(self.vision_client, "analyze")
        if inspect.iscoroutinefunction(analyze):
            vision_result: VisionOutputModel = await analyze(image_bytes)
        else:
            vision_result = await asyncio.to_thread(analyze, image_bytes)

        ph_predicted = vision_result.ph_predicted
        species = vision_result.species
        condition = vision_result.condition
        severity = vision_result.severity
        timestamp = datetime.utcnow().isoformat() + "Z"

        diagnostic_dict = {
            "plant_id": plant_id,
            "species": species,
            "condition": condition,
            "severity": severity,
            "ph_predicted": ph_predicted,
            "timestamp": timestamp,
            "raw": vision_result.model_dump(),
        }

        # 2. Persist diagnostic (support sync or async save)
        save_fn = getattr(self.diagnostic_repo, "save_diagnostic")
        if inspect.iscoroutinefunction(save_fn):
            saved_id = await save_fn(diagnostic_dict)
        else:
            saved_id = await asyncio.to_thread(save_fn, diagnostic_dict)

        # attach id if returned
        if saved_id is not None:
            diagnostic_dict["id"] = saved_id

        # 3. Fire-and-forget: PATCH Django with ph_level if available
        logger = logging.getLogger("ms1_vision.usecases.create_diagnostic")
        if ph_predicted is not None:
            try:
                if hasattr(self.django_patch_client, "schedule_patch"):
                    # include token when scheduling
                    try:
                        self.django_patch_client.schedule_patch(f"/api/v1/sensor-data/{saved_id}/", {"ph_level": ph_predicted}, token=token)
                    except RuntimeError:
                        # fallback to explicit task scheduling
                        asyncio.create_task(self.django_patch_client.patch_ph_level(str(saved_id), ph_predicted, token=token))
                elif hasattr(self.django_patch_client, "patch_ph_level"):
                    asyncio.create_task(self.django_patch_client.patch_ph_level(str(saved_id), ph_predicted, token=token))
            except Exception as e:
                logger.error("Failed to schedule patch to Django: %s", e, exc_info=True)

        # 4. Fire-and-forget: publish to Redis pub/sub
        try:
            payload = {
                "plant_id": plant_id,
                "species": species,
                "condition": condition,
                "severity": severity,
                "ph_predicted": ph_predicted,
                "timestamp": timestamp,
            }
            if hasattr(self.redis_publisher, "publish_diagnostic"):
                try:
                    asyncio.create_task(self.redis_publisher.publish_diagnostic(payload))
                except RuntimeError:
                    # Attempt to run in executor (sync fallback)
                    try:
                        asyncio.get_event_loop().run_in_executor(None, self.redis_publisher.publish_diagnostic, payload)
                    except Exception as e:
                        logger.error("Redis publish failed (fallback): %s", e, exc_info=True)
        except Exception as e:
            logger.error("Unexpected error preparing redis publish: %s", e, exc_info=True)

        # Build Pydantic DiagnosticModel and return
        return DiagnosticModel.model_validate(diagnostic_dict)
