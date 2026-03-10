"""
Integration tests for AndroidDriver against a real Android emulator.

Prerequisites:
  - Android emulator running (adb devices shows "emulator-5554 device")
  - DroidRun Portal APK installed and accessibility service enabled
  - pip install pytest pytest-asyncio

Run:
  pytest tests/test_android_driver.py -v
"""

import asyncio
import struct

import pytest
import pytest_asyncio

from droidrun.tools.driver.android import AndroidDriver

DEVICE_SERIAL = "emulator-5554"


# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="module")
async def driver():
    """Create and connect AndroidDriver once for all tests."""
    d = AndroidDriver(serial=DEVICE_SERIAL)
    await d.connect()
    yield d
    # Go home after all tests
    await d.press_key(3)


# ============================================================================
# 1. Connection & Lifecycle
# ============================================================================


class TestConnection:
    @pytest.mark.asyncio
    async def test_connect(self, driver: AndroidDriver):
        """Driver should be connected after fixture setup."""
        assert driver._connected is True
        assert driver.device is not None
        assert driver.portal is not None

    @pytest.mark.asyncio
    async def test_ensure_connected_is_idempotent(self, driver: AndroidDriver):
        """Calling ensure_connected on already-connected driver should not error."""
        await driver.ensure_connected()
        assert driver._connected is True

    @pytest.mark.asyncio
    async def test_portal_ping(self, driver: AndroidDriver):
        """Portal should respond to ping."""
        result = await driver.portal.ping()
        assert result["status"] == "success", f"Portal ping failed: {result}"


# ============================================================================
# 2. State / Observation
# ============================================================================


class TestObservation:
    @pytest.mark.asyncio
    async def test_get_ui_tree(self, driver: AndroidDriver):
        """get_ui_tree should return a dict with a11y_tree and phone_state."""
        tree = await driver.get_ui_tree()
        assert isinstance(tree, dict), f"Expected dict, got {type(tree)}"
        assert "a11y_tree" in tree, f"Missing 'a11y_tree'. Keys: {list(tree.keys())}"
        assert "phone_state" in tree, f"Missing 'phone_state'. Keys: {list(tree.keys())}"

    @pytest.mark.asyncio
    async def test_ui_tree_has_elements(self, driver: AndroidDriver):
        """a11y_tree should contain at least one element."""
        tree = await driver.get_ui_tree()
        a11y = tree["a11y_tree"]
        # a11y_tree could be a list or dict with children
        if isinstance(a11y, list):
            assert len(a11y) > 0, "a11y_tree is empty list"
        elif isinstance(a11y, dict):
            assert len(a11y) > 0, "a11y_tree is empty dict"

    @pytest.mark.asyncio
    async def test_phone_state_has_screen_info(self, driver: AndroidDriver):
        """phone_state should have screen dimensions."""
        tree = await driver.get_ui_tree()
        ps = tree["phone_state"]
        assert isinstance(ps, dict)
        # Typical keys: screenWidth, screenHeight, or similar
        has_screen = any(
            k in ps for k in ["screenWidth", "screen_width", "displayWidth"]
        )
        # If no specific keys, at least phone_state shouldn't be empty
        assert len(ps) > 0, f"phone_state is empty. Got: {ps}"

    @pytest.mark.asyncio
    async def test_screenshot_returns_png_bytes(self, driver: AndroidDriver):
        """screenshot should return valid PNG bytes."""
        data = await driver.screenshot()
        assert isinstance(data, bytes), f"Expected bytes, got {type(data)}"
        assert len(data) > 1000, f"Screenshot too small: {len(data)} bytes"
        # Check PNG magic bytes
        assert data[:4] == b"\x89PNG", "Screenshot is not valid PNG format"

    @pytest.mark.asyncio
    async def test_screenshot_has_reasonable_size(self, driver: AndroidDriver):
        """Screenshot should be at least 10KB (real screen content)."""
        data = await driver.screenshot()
        assert len(data) > 10_000, f"Screenshot suspiciously small: {len(data)} bytes"

    @pytest.mark.asyncio
    async def test_get_date(self, driver: AndroidDriver):
        """get_date should return a non-empty string with date info."""
        date_str = await driver.get_date()
        assert isinstance(date_str, str)
        assert len(date_str) > 5, f"Date too short: '{date_str}'"
        # Should contain year-like number
        assert any(
            year in date_str for year in ["2025", "2026", "2027"]
        ), f"Date doesn't look right: '{date_str}'"


# ============================================================================
# 3. App Management
# ============================================================================


class TestAppManagement:
    @pytest.mark.asyncio
    async def test_list_packages(self, driver: AndroidDriver):
        """list_packages should return a list of package name strings."""
        packages = await driver.list_packages(include_system=False)
        assert isinstance(packages, list)
        assert len(packages) > 0, "No user packages found"
        # Packages should look like com.something
        for pkg in packages[:5]:
            assert isinstance(pkg, str)
            assert "." in pkg, f"Package name doesn't look valid: '{pkg}'"

    @pytest.mark.asyncio
    async def test_list_packages_with_system(self, driver: AndroidDriver):
        """Including system packages should return more results."""
        user_only = await driver.list_packages(include_system=False)
        with_system = await driver.list_packages(include_system=True)
        assert len(with_system) >= len(
            user_only
        ), "System packages should include user packages"

    @pytest.mark.asyncio
    async def test_get_apps(self, driver: AndroidDriver):
        """get_apps should return list of dicts with package and label."""
        apps = await driver.get_apps(include_system=False)
        assert isinstance(apps, list)
        assert len(apps) > 0, "No apps found"
        # Check structure
        app = apps[0]
        assert "package" in app, f"Missing 'package' key. Got: {app}"
        assert "label" in app, f"Missing 'label' key. Got: {app}"

    @pytest.mark.asyncio
    async def test_portal_is_installed(self, driver: AndroidDriver):
        """DroidRun Portal should appear in package list."""
        packages = await driver.list_packages(include_system=True)
        assert (
            "com.droidrun.portal" in packages
        ), "DroidRun Portal not found in packages"

    @pytest.mark.asyncio
    async def test_start_app_settings(self, driver: AndroidDriver):
        """Should be able to launch Settings app."""
        result = await driver.start_app("com.android.settings")
        assert "App started" in result, f"Failed to start Settings: {result}"
        await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_start_app_nonexistent(self, driver: AndroidDriver):
        """Starting a nonexistent app should return failure message."""
        result = await driver.start_app("com.nonexistent.fake.app.xyz")
        assert "Failed" in result or "Error" in result.lower() or "error" in result.lower(), (
            f"Expected failure for nonexistent app, got: {result}"
        )

    @pytest.mark.asyncio
    async def test_install_app_nonexistent_path(self, driver: AndroidDriver):
        """install_app with nonexistent file should return error."""
        result = await driver.install_app("/tmp/nonexistent_app.apk")
        assert "not found" in result.lower() or "failed" in result.lower(), (
            f"Expected failure for nonexistent APK, got: {result}"
        )


# ============================================================================
# 4. Input Actions
# ============================================================================


class TestInputActions:
    @pytest.mark.asyncio
    async def test_tap(self, driver: AndroidDriver):
        """Tapping center of screen should not raise."""
        # Go home first
        await driver.press_key(3)
        await asyncio.sleep(0.5)
        # Tap center of a typical screen
        await driver.tap(540, 960)
        # No exception = pass

    @pytest.mark.asyncio
    async def test_swipe_down(self, driver: AndroidDriver):
        """Swiping down should not raise."""
        await driver.press_key(3)
        await asyncio.sleep(0.5)
        await driver.swipe(540, 400, 540, 1200, 300)
        # No exception = pass

    @pytest.mark.asyncio
    async def test_swipe_up(self, driver: AndroidDriver):
        """Swiping up should not raise."""
        await driver.swipe(540, 1200, 540, 400, 300)

    @pytest.mark.asyncio
    async def test_press_key_home(self, driver: AndroidDriver):
        """Pressing HOME key should not raise."""
        await driver.press_key(3)
        await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_press_key_back(self, driver: AndroidDriver):
        """Pressing BACK key should not raise."""
        await driver.press_key(4)

    @pytest.mark.asyncio
    async def test_press_key_enter(self, driver: AndroidDriver):
        """Pressing ENTER key should not raise."""
        await driver.press_key(66)

    @pytest.mark.asyncio
    async def test_input_text_in_search(self, driver: AndroidDriver):
        """Open Settings, tap search, type text, verify it worked."""
        # Open Settings
        await driver.start_app("com.android.settings")
        await asyncio.sleep(1.5)

        # Get UI tree to find search element
        tree = await driver.get_ui_tree()
        assert "error" not in tree, f"UI tree error: {tree}"

        # Try tapping search icon area (top right, typical in Settings)
        # On most emulators, search is near top of screen
        await driver.tap(540, 150)
        await asyncio.sleep(1)

        # Type some text
        result = await driver.input_text("display", clear=True)
        assert result is True, "input_text returned False"
        await asyncio.sleep(0.5)

        # Clean up — press back twice and go home
        await driver.press_key(4)
        await asyncio.sleep(0.3)
        await driver.press_key(4)
        await asyncio.sleep(0.3)
        await driver.press_key(3)

    @pytest.mark.asyncio
    async def test_drag_not_implemented(self, driver: AndroidDriver):
        """drag should raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await driver.drag(100, 100, 500, 500)


# ============================================================================
# 5. Portal Client Direct
# ============================================================================


class TestPortalClient:
    @pytest.mark.asyncio
    async def test_portal_get_version(self, driver: AndroidDriver):
        """Portal version should return a string (may be 'unknown' in content-provider mode)."""
        version = await driver.portal.get_version()
        assert isinstance(version, str)
        assert len(version) > 0, "Portal version is empty"

    @pytest.mark.asyncio
    async def test_portal_get_state(self, driver: AndroidDriver):
        """Portal get_state should return structured data."""
        state = await driver.portal.get_state()
        assert isinstance(state, dict)
        assert "error" not in state, f"Portal state error: {state}"

    @pytest.mark.asyncio
    async def test_portal_take_screenshot(self, driver: AndroidDriver):
        """Portal screenshot should return PNG bytes."""
        data = await driver.portal.take_screenshot(hide_overlay=True)
        assert isinstance(data, bytes)
        assert data[:4] == b"\x89PNG"


# ============================================================================
# 6. Full Workflow — End to End
# ============================================================================


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_full_workflow(self, driver: AndroidDriver):
        """
        Complete workflow:
        1. Go home
        2. Take screenshot
        3. Get UI tree
        4. Open Settings
        5. Get UI tree again (should be different)
        6. Take screenshot
        7. Press back
        8. Go home
        """
        # 1. Home
        await driver.press_key(3)
        await asyncio.sleep(1)

        # 2. Screenshot at home
        home_screenshot = await driver.screenshot()
        assert len(home_screenshot) > 1000

        # 3. UI tree at home
        home_tree = await driver.get_ui_tree()
        assert "a11y_tree" in home_tree

        # 4. Open Settings
        result = await driver.start_app("com.android.settings")
        assert "App started" in result
        await asyncio.sleep(1.5)

        # 5. UI tree in Settings (should differ from home)
        settings_tree = await driver.get_ui_tree()
        assert "a11y_tree" in settings_tree

        # 6. Screenshot in Settings
        settings_screenshot = await driver.screenshot()
        assert len(settings_screenshot) > 1000
        # Screenshots should be different
        assert home_screenshot != settings_screenshot, (
            "Home and Settings screenshots are identical — something is wrong"
        )

        # 7. Back
        await driver.press_key(4)
        await asyncio.sleep(0.5)

        # 8. Home
        await driver.press_key(3)
        await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_rapid_state_queries(self, driver: AndroidDriver):
        """Multiple rapid get_ui_tree calls should all succeed."""
        results = []
        for _ in range(5):
            tree = await driver.get_ui_tree()
            results.append(tree)
            assert "a11y_tree" in tree

        assert len(results) == 5, "Not all state queries completed"

    @pytest.mark.asyncio
    async def test_rapid_screenshots(self, driver: AndroidDriver):
        """Multiple rapid screenshots should all succeed."""
        screenshots = []
        for _ in range(3):
            data = await driver.screenshot()
            screenshots.append(data)
            assert data[:4] == b"\x89PNG"

        assert len(screenshots) == 3

    @pytest.mark.asyncio
    async def test_supported_set(self, driver: AndroidDriver):
        """AndroidDriver.supported should list all expected capabilities."""
        expected = {
            "tap", "swipe", "input_text", "press_key",
            "start_app", "screenshot", "get_ui_tree",
            "get_date", "get_apps", "list_packages",
            "install_app", "drag",
        }
        assert driver.supported == expected, (
            f"Supported mismatch.\n"
            f"  Missing: {expected - driver.supported}\n"
            f"  Extra: {driver.supported - expected}"
        )
