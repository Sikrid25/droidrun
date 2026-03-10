"""
Droidrun - A framework for controlling Android devices.
"""

import logging
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("droidrun")
except PackageNotFoundError:
    __version__ = "0.5.1"

from droidrun.log_handlers import CLILogHandler

_logger = logging.getLogger("droidrun")
_logger.addHandler(CLILogHandler())
_logger.setLevel(logging.INFO)
_logger.propagate = False

# Device drivers and UI state
from droidrun.tools import (
    AndroidDriver,
    DeviceDriver,
    RecordingDriver,
    StateProvider,
    AndroidStateProvider,
    UIState,
)

__all__ = [
    "DeviceDriver",
    "AndroidDriver",
    "RecordingDriver",
    "StateProvider",
    "AndroidStateProvider",
    "UIState",
]
