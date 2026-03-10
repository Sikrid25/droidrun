"""Device driver abstractions for DroidRun."""

from droidrun.tools.driver.android import AndroidDriver
from droidrun.tools.driver.base import DeviceDisconnectedError, DeviceDriver
from droidrun.tools.driver.recording import RecordingDriver

# Optional drivers — require extra dependencies
try:
    from droidrun.tools.driver.cloud import CloudDriver
except ImportError:
    CloudDriver = None

try:
    from droidrun.tools.driver.ios import IOSDriver
except ImportError:
    IOSDriver = None

try:
    from droidrun.tools.driver.stealth import StealthDriver
except ImportError:
    StealthDriver = None

__all__ = [
    "DeviceDisconnectedError",
    "DeviceDriver",
    "AndroidDriver",
    "RecordingDriver",
]
