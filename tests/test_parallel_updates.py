"""Every platform says how many updates may run at once: reads freely, commands one at a time."""

from __future__ import annotations

import importlib

import pytest

READ_ONLY = ("binary_sensor", "device_tracker", "sensor")
COMMANDS = ("button", "climate", "lock", "number", "select", "switch")


@pytest.mark.parametrize("platform", READ_ONLY)
def test_reading_platforms_do_not_queue(platform):
    module = importlib.import_module(f"custom_components.audiconnect.{platform}")
    assert module.PARALLEL_UPDATES == 0


@pytest.mark.parametrize("platform", COMMANDS)
def test_platforms_that_command_the_car_go_one_at_a_time(platform):
    module = importlib.import_module(f"custom_components.audiconnect.{platform}")
    assert module.PARALLEL_UPDATES == 1
