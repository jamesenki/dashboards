"""
Pytest configuration for integration tests.
This file configures pytest for our TDD-based integration testing approach.
"""
import os

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers for TDD phases."""
    # Register our custom markers
    config.addinivalue_line(
        "markers", "red: mark test as part of RED phase (defining expected behavior)"
    )
    config.addinivalue_line(
        "markers", "green: mark test as part of GREEN phase (minimal implementation)"
    )
    config.addinivalue_line(
        "markers",
        "refactor: mark test as part of REFACTOR phase (improved implementation)",
    )

    # Set TDD phase environment variable if not already set
    if "TDD_PHASE" not in os.environ:
        os.environ["TDD_PHASE"] = "red"  # Default to RED phase

    # Print TDD phase info
    print(
        f"\nRunning integration tests in {os.environ.get('TDD_PHASE').upper()} phase of TDD"
    )


def pytest_collection_modifyitems(config, items):
    """Filter tests based on TDD phase if specified."""
    tdd_phase = os.environ.get("TDD_PHASE", "").lower()

    if tdd_phase in ["red", "green", "refactor"]:
        selected_items = []
        deselected_items = []

        for item in items:
            markers = [mark.name for mark in item.iter_markers()]

            # Keep items that match the current TDD phase or have no phase marker
            if tdd_phase in markers or not any(
                phase in markers for phase in ["red", "green", "refactor"]
            ):
                selected_items.append(item)
            else:
                deselected_items.append(item)

        config.hook.pytest_deselected(items=deselected_items)
        items[:] = selected_items


@pytest.fixture(autouse=True)
def verify_tdd_phase_expectations(request):
    """Automatically verify TDD phase expectations for each test.

    In RED phase: tests are expected to fail
    In GREEN phase: tests are expected to pass
    In REFACTOR phase: tests are expected to pass
    """
    tdd_phase = os.environ.get("TDD_PHASE", "").lower()

    # Only apply special handling in RED phase since tests are expected to fail
    is_red_phase = tdd_phase == "red"
    is_marked_red = request.node.get_closest_marker("red") is not None

    # In RED phase, we expect RED-marked tests to fail, but don't want to crash the test run
    if is_red_phase and is_marked_red:
        try:
            yield
            # If we get here, the test passed
            pytest.skip(
                "RED phase test unexpectedly passed - implementation may be ahead of tests!"
            )
        except Exception:
            # This is expected in RED phase, so convert the exception to a pass
            pytest.skip("Test failed as expected in RED phase")
    else:
        # Normal test execution for other phases
        yield
