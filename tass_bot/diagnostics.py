# tass_bot/diagnostics.py
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver

def take_screenshot(driver: WebDriver, base_download_path: Path, filename: str):
    """Joriy brauzer oynasining skrinshotini oladi."""
    screenshot_dir = base_download_path / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / filename
    try:
        driver.save_screenshot(str(path))
        print(f"📸 Skrinshot saqlandi: {path}")
    except Exception as e:
        print(f"❌ Skrinshot olishda xatolik: {e}")

def get_page_source(driver: WebDriver, base_download_path: Path, filename: str):
    """Joriy sahifaning HTML manbasini saqlaydi."""
    source_dir = base_download_path / "page_sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    path = source_dir / filename
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"📄 HTML manba saqlandi: {path}")
    except Exception as e:
        print(f"❌ HTML manbani saqlashda xatolik: {e}")
