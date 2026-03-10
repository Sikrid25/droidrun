# DroidRun — Android Device Driver

A Python library for controlling Android devices programmatically via ADB and [DroidRun Portal](https://github.com/droidrun/droidrun-portal).

This is a stripped-down version of the [DroidRun framework](https://github.com/droidrun/droidrun) — all LLM agent, CLI, and telemetry components have been removed. What remains is a clean, async device driver for Android automation.

## How It Works

DroidRun Portal is an Android APK that runs as an accessibility service on the device. It exposes the UI tree, text input, and screenshot capabilities through ADB (content provider or TCP).

This library (`AndroidDriver`) communicates with the Portal via ADB to control the device.

```
Your Python script
    → AndroidDriver (this library)
        → ADB
            → DroidRun Portal APK (on device)
                → Android Accessibility Service
```

## Installation

```bash
pip install -e .
```

**Requirements:** Python 3.11 – 3.13

## Quick Start

```python
import asyncio
from droidrun import AndroidDriver

async def main():
    driver = AndroidDriver(serial="emulator-5554")
    await driver.connect()

    # Tap a point on screen
    await driver.tap(500, 300)

    # Type text into focused field
    await driver.input_text("hello world")

    # Swipe down
    await driver.swipe(500, 300, 500, 1200, 300)

    # Press back button
    await driver.press_key(4)

    # Get UI accessibility tree
    ui_tree = await driver.get_ui_tree()

    # Take screenshot (PNG bytes)
    screenshot = await driver.screenshot()

    # Launch an app
    await driver.start_app("com.android.settings")

asyncio.run(main())
```

## Portal Setup

The DroidRun Portal APK must be installed and its accessibility service enabled before use:

```python
from droidrun.portal import setup_portal
from async_adbutils import adb

async def setup():
    device = await adb.device(serial="emulator-5554")
    await setup_portal(device, debug=False)
```

## API Reference

### AndroidDriver

| Method | Description |
|--------|-------------|
| `connect()` | Connect to device via ADB and Portal |
| `tap(x, y)` | Tap at screen coordinates |
| `swipe(x1, y1, x2, y2, duration_ms)` | Swipe gesture |
| `input_text(text, clear)` | Type text into focused input |
| `press_key(keycode)` | Send keyevent (4=back, 3=home, 66=enter) |
| `start_app(package, activity?)` | Launch an application |
| `install_app(path)` | Install APK from file path |
| `get_apps(include_system)` | List installed apps with labels |
| `list_packages(include_system)` | List package names |
| `screenshot(hide_overlay)` | Capture screen as PNG bytes |
| `get_ui_tree()` | Get accessibility tree as dict |
| `get_date()` | Get device date/time |

### Other Classes

| Class | Purpose |
|-------|---------|
| `DeviceDriver` | Abstract base class for all drivers |
| `RecordingDriver` | Replay recorded action sequences |
| `StateProvider` | Orchestrates UI state fetching + filtering |
| `UIState` | Snapshot of screen elements |

## Dependencies

| Package | Purpose |
|---------|---------|
| `async_adbutils` | ADB communication |
| `pydantic` | Data validation |
| `rich` | Console output |
| `httpx` | HTTP client (Portal TCP mode) |
| `aiofiles` | Async file operations |
| `requests` | Portal APK download |

## Based On

This is a fork of [droidrun/droidrun](https://github.com/droidrun/droidrun) v0.5.1, retaining only the device driver layer (`droidrun/tools/` and `droidrun/portal.py`).

## License

MIT
