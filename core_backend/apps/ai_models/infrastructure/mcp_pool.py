"""Pool persistente de sesiones MCP para Django (host) → mole_chat (SSE).

Diseño:
- Un único event loop asyncio corre en un daemon thread por proceso worker.
- Dentro de ese loop se mantienen MCP_POOL_SIZE sesiones SSE persistentes; cada
  sesión es un par (sse_client streams, ClientSession) inicializado una sola vez.
- JSON-RPC 2.0 multiplexa llamadas concurrentes sobre la misma sesión mediante
  ids únicos; el SDK se encarga del enrutamiento de respuestas.
- Los workers WSGI/Gunicorn sincrónicos envían corutinas al loop daemon con
  asyncio.run_coroutine_threadsafe(...) y esperan el concurrent.futures.Future.
  No hay asyncio.Lock ni colas de préstamo alrededor de la inferencia.
- Selección Round-Robin atómica (threading.Lock solo para incrementar índice).
- Reconexión lazy por slot si una sesión muere; fallback a sesión efímera como
  último recurso para nunca dejar al usuario sin respuesta.
"""
from __future__ import annotations

import asyncio
import itertools
import logging
import threading
import time
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from django.conf import settings
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


class _SessionSlot:
    """Contenedor de una sesión MCP viva."""

    def __init__(self) -> None:
        self.session: ClientSession | None = None
        self.ready_event = threading.Event()
        # Protege reconexión concurrente del *mismo* slot, no bloquea inferencia.
        self.lock = asyncio.Lock()


class MCPConnectionPool:
    """Singleton por proceso worker que mantiene N sesiones MCP persistentes."""

    _instance: MCPConnectionPool | None = None
    _lock = threading.Lock()

    def __new__(cls) -> MCPConnectionPool:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._base_url = getattr(settings, "MCP_CHAT_URL", "http://ms2_chat:8002/mcp")
        self._timeout = float(getattr(settings, "MCP_TIMEOUT", 60))
        self._pool_size = max(1, int(getattr(settings, "MCP_POOL_SIZE", 3)))
        self._slots: list[_SessionSlot] = []
        self._round_robin = itertools.cycle(range(self._pool_size))
        self._rr_lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._shutdown_event: asyncio.Event | None = None
        self._session_tasks: list[asyncio.Task] = []
        self._initialized = True

    def _start_loop(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        def run_loop():
            loop = asyncio.new_event_loop()
            self._loop = loop
            self._shutdown_event = asyncio.Event()
            asyncio.set_event_loop(loop)
            logger.info("MCP daemon loop started")
            try:
                loop.run_forever()
            finally:
                if self._shutdown_event is not None and not self._shutdown_event.is_set():
                    self._shutdown_event.set()
                # Esperar a que las tareas de sesión cierren sus contextos.
                if self._session_tasks:
                    loop.run_until_complete(
                        asyncio.gather(*self._session_tasks, return_exceptions=True)
                    )
                loop.close()
                logger.info("MCP daemon loop stopped")

        self._thread = threading.Thread(target=run_loop, name="mcp-daemon", daemon=True)
        self._thread.start()

        while self._loop is None:
            pass

        self._slots = [_SessionSlot() for _ in range(self._pool_size)]
        setup_future = asyncio.run_coroutine_threadsafe(self._setup_pool(), self._loop)
        try:
            setup_future.result(timeout=15)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to setup MCP pool: %s", exc)

    async def _setup_pool(self) -> None:
        """Crea las tareas persistentes del pool dentro del loop daemon."""
        assert self._loop is not None
        self._session_tasks = [
            self._loop.create_task(self._open_slot(i)) for i in range(self._pool_size)
        ]
        # Esperar a que cada slot esté listo (o haya fallado) antes de continuar.
        for slot in self._slots:
            deadline = time.monotonic() + 10
            while not slot.ready_event.is_set() and time.monotonic() < deadline:
                await asyncio.sleep(0.05)

    def _ensure_started(self) -> None:
        if self._loop is None or not self._thread or not self._thread.is_alive():
            self._start_loop()

    async def _open_slot(self, index: int) -> None:
        """Abre sse_client + ClientSession y los mantiene vivos en el loop."""
        slot = self._slots[index]
        url = f"{self._base_url}/v1/sse"
        try:
            async with sse_client(url=url, timeout=self._timeout) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    slot.session = session
                    slot.ready_event.set()
                    logger.info("MCP session slot %d ready", index)
                    assert self._shutdown_event is not None
                    await self._shutdown_event.wait()
        except Exception as exc:  # noqa: BLE001
            logger.error("MCP session slot %d failed: %s", index, exc)
            slot.ready_event.clear()
            slot.session = None
            raise

    def _select_index(self) -> int:
        with self._rr_lock:
            return next(self._round_robin)

    def _healthy_slots(self) -> list[int]:
        return [
            i
            for i, slot in enumerate(self._slots)
            if slot.ready_event.is_set() and slot.session is not None
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Llama a una tool MCP de forma sincrónica desde un worker WSGI.

        Selecciona una sesión vía Round-Robin y envía la corutina al loop
        daemon. No bloquea otras peticiones: el SDK multiplexa por id.
        """
        self._ensure_started()
        if self._loop is None:
            raise RuntimeError("MCP loop not available")

        healthy = self._healthy_slots()
        if not healthy:
            logger.warning("No healthy MCP sessions; falling back to ephemeral session")
            return self._ephemeral_call(name, arguments)

        idx = self._select_index() % len(healthy)
        slot_index = healthy[idx]
        slot = self._slots[slot_index]

        async def _call():
            async with slot.lock:
                if slot.session is None:
                    raise RuntimeError("MCP session became unavailable")
                return await slot.session.call_tool(name, arguments=arguments)

        future = asyncio.run_coroutine_threadsafe(_call(), self._loop)
        try:
            return future.result(timeout=self._timeout)
        except FutureTimeoutError as exc:
            logger.error("MCP call_tool timeout")
            future.cancel()
            raise RuntimeError("MCP call_tool timeout") from exc
        except Exception as exc:  # noqa: BLE001
            logger.warning("MCP call failed on slot %d: %s", slot_index, exc)
            slot.ready_event.clear()
            asyncio.run_coroutine_threadsafe(self._reopen_slot(slot_index), self._loop)
            # Reintentar una sola vez contra otro slot.
            return self.call_tool(name, arguments)

    async def _reopen_slot(self, index: int) -> None:
        # Esperar a que el slot previo libere el lock (si estaba en uso) y luego reabrir.
        await asyncio.sleep(0)
        try:
            await self._open_slot(index)
        except Exception as exc:  # noqa: BLE001
            logger.error("MCP slot %d reopen failed: %s", index, exc)

    def _ephemeral_call(self, name: str, arguments: dict[str, Any]) -> Any:
        """Fallback: abre una sesión efímera si todas las persistentes cayeron."""

        async def _call():
            url = f"{self._base_url}/v1/sse"
            async with sse_client(url=url, timeout=self._timeout) as (rs, ws):
                async with ClientSession(rs, ws) as session:
                    await session.initialize()
                    return await session.call_tool(name, arguments=arguments)

        try:
            return asyncio.run(_call())
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"MCP ephemeral call failed: {exc}") from exc

    def stop(self) -> None:
        """Detiene el loop daemon y cierra todas las sesiones."""
        if self._loop is None or self._shutdown_event is None:
            return
        logger.info("Stopping MCP daemon loop")
        self._loop.call_soon_threadsafe(self._shutdown_event.set)
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)


# Hook de shutdown para Gunicorn/Celery workers.
_pool = MCPConnectionPool()


def shutdown_mcp_pool() -> None:
    _pool.stop()
