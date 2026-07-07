"""Shared test fixtures and marker configuration."""

import pytest


def pytest_configure(config):
    """Register the `integration` marker for tests requiring Docker containers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require Docker containers (PostgreSQL+pgvector, Redis). "
        "Skipped by default; run with `pytest --run-integration`.",
    )


def pytest_addoption(parser):
    """Add a CLI flag to run integration tests."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require Docker containers",
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration is passed."""
    if config.getoption("--run-integration"):
        return  # run all tests
    skip_integration = pytest.mark.skip(reason="Use --run-integration to run Docker-dependent tests")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
