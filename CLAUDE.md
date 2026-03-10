# DroidRun — Android Device Driver

Stripped-down version of [DroidRun](https://github.com/droidrun/droidrun) — เหลือเฉพาะ **device driver layer** สำหรับควบคุม Android ผ่าน [DroidRun Portal](https://github.com/droidrun/droidrun-portal) (accessibility service APK ที่ติดตั้งบนเครื่อง)

ตัด LLM agents, CLI, telemetry, config system ทั้งหมดออก — ใช้เป็น Python library สำหรับ automation เท่านั้น

## How It Works

```
Python script → AndroidDriver → ADB → DroidRun Portal APK (on device)
                                         ↓
                                  Accessibility Service
                                  (UI tree, tap, type, screenshot)
```

DroidRun Portal คือ APK ที่รันบน Android เป็น accessibility service — ทำให้อ่าน UI tree, input text, จับ screenshot ได้ผ่าน ADB content provider หรือ TCP

## Project Structure

```
droidrun/
├── __init__.py             # Package exports
├── log_handlers.py         # Rich console logging
├── portal.py               # Portal APK download/install/setup
└── tools/
    ├── __init__.py          # Public API
    ├── driver/
    │   ├── base.py          # DeviceDriver — abstract interface
    │   ├── android.py       # AndroidDriver — ADB + Portal
    │   ├── ios.py           # IOSDriver (optional, needs extra deps)
    │   ├── cloud.py         # CloudDriver (optional, needs mobilerun-sdk)
    │   ├── recording.py     # RecordingDriver — replay testing
    │   └── stealth.py       # StealthDriver (optional)
    ├── ui/                  # UI state: StateProvider, UIState
    ├── filters/             # UI tree filtering
    ├── formatters/          # UI tree formatting
    ├── android/             # PortalClient — Portal HTTP/content-provider comms
    ├── ios/                 # iOS-specific tools
    └── helpers/             # Geometry utilities
```

## AndroidDriver API

```python
from droidrun import AndroidDriver

driver = AndroidDriver(serial="emulator-5554", use_tcp=False)
await driver.connect()

# Input
await driver.tap(x, y)
await driver.swipe(x1, y1, x2, y2, duration_ms)
await driver.input_text("text", clear=False)
await driver.press_key(keycode)       # 4=back, 3=home, 66=enter

# Apps
await driver.start_app("com.example.app")
await driver.install_app("/path/to.apk")
await driver.get_apps(include_system=True)
await driver.list_packages(include_system=False)

# Observation
await driver.screenshot(hide_overlay=True)  # → bytes (PNG)
await driver.get_ui_tree()                  # → dict
await driver.get_date()                     # → str
```

## Portal Setup

Portal APK ต้องติดตั้งและเปิด accessibility service ก่อนใช้งาน:

```python
from droidrun.portal import setup_portal
from async_adbutils import adb

device = await adb.device(serial="emulator-5554")
await setup_portal(device, debug=False)
```

## Dependencies

`async_adbutils`, `pydantic`, `rich`, `httpx`, `aiofiles`, `python-dotenv`, `requests`

## Development

```bash
pip install -e ".[dev]"
black .              # format
ruff check droidrun/ # lint
```
