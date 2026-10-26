import os
import sys
import ctypes
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv

# Base project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(PROJECT_ROOT / ".env")

class Settings:
    """Central configuration for tests and environments."""
    BASE_URL: str = os.getenv("BASE_URL", "https://staging.app.n3xora.net").rstrip("/")
    LOGIN_PATH: str = os.getenv("LOGIN_PATH", "/ttenant/login")
    DASHBOARD_PATH: str = os.getenv("DASHBOARD_PATH", "/tenant/ttenant/admin/dashboard")

    TEST_USER_EMAIL: str = os.getenv("TEST_USER_EMAIL", "ttenant@gmail.com")
    TEST_USER_PASSWORD: str = os.getenv("TEST_USER_PASSWORD", "12345678")

    MERCHANT_EMAIL: str = os.getenv("MERCHANT_EMAIL", "b2c@merchant.com")
    MERCHANT_PASSWORD: str = os.getenv("MERCHANT_PASSWORD", "123456789")

    DRIVER_EMAIL: str = os.getenv("DRIVER_EMAIL", "b2c@driver.com")
    DRIVER_PASSWORD: str = os.getenv("DRIVER_PASSWORD", "12345678")

    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
    BROWSER: str = os.getenv("BROWSER", "chromium")
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30000"))
    DEFAULT_ZOOM: str = os.getenv("DEFAULT_ZOOM", "67%")

    @classmethod
    def get_login_url(cls) -> str:
        return f"{cls.BASE_URL}{cls.LOGIN_PATH}"

    @classmethod
    def get_dashboard_url(cls) -> str:
        return f"{cls.BASE_URL}{cls.DASHBOARD_PATH}"

    @classmethod
    def get_screen_dimensions(cls) -> Dict[str, int]:
        """Detect and return screen width and height to fit the screen."""
        try:
            if sys.platform == "win32":
                user32 = ctypes.windll.user32
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except Exception:
                    try:
                        user32.SetProcessDPIAware()
                    except Exception:
                        pass
                w = user32.GetSystemMetrics(0)
                h = user32.GetSystemMetrics(1)
                if w > 0 and h > 0:
                    return {"width": w, "height": h}
        except Exception:
            pass
        return {"width": 1920, "height": 1080}

settings = Settings()
