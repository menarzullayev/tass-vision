# tass_bot/bot_core.py
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# --- Yangi va mavjud modullardan funksiyalarni import qilish ---

# config.py dan global sozlamalarni import qilish (loyihangizda bu fayl bor deb taxmin qilinadi)
# Agar config.py fayli bo'lmasa, uni yarating va ichiga BASE_DOWNLOAD_PATH = Path("downloads") deb yozing.
try:
    from config import BASE_DOWNLOAD_PATH
except ImportError:
    print("⚠️ 'config.py' topilmadi yoki unda 'BASE_DOWNLOAD_PATH' o'zgaruvchisi yo'q. Standart 'downloads' papkasi ishlatiladi.")
    BASE_DOWNLOAD_PATH = Path("downloads")

from .authentication import login_with_selenium
from .export_process import run_export_process_for_page_cameras, _update_download_directory, _wait_for_download_complete
from .diagnostics import take_screenshot, get_page_source
from .page_navigator import get_total_pages, navigate_to_page
from .camera_processor import process_current_page


def get_filtered_cameras_generator(self):
    """
    Bu generator funksiya sahifalarni aylanib chiqadi, ma'lumotlarni filtrlaydi va
    page_navigator hamda camera_processor modullarini boshqaradi.
    U avvalgi `get_filtered_cameras_by_page` funksiyasining o'rnini bosadi.
    
    Yields:
        list[dict]: Joriy sahifadagi filtrlangan kameralar ro'yxati.
    """
    if not self.driver:
        print("❌ WebDriver ishga tushmagan, kameralarni o'qish mumkin emas.")
        return

    print(f"\n🔍 Kameralar sahifasiga o'tilmoqda: {self.CAMERAS_PAGE_URL}")
    self.driver.get(self.CAMERAS_PAGE_URL)
    
    try:
        WebDriverWait(self.driver, 30).until(EC.url_to_be(self.CAMERAS_PAGE_URL))
        print("✅ Kameralar sahifasi muvaffaqiyatli yuklandi.")

        main_window_handle = self.driver.current_window_handle
        total_pages = get_total_pages(self.driver, self.base_download_path)

        for page_num in range(1, total_pages + 1):
            print(f"\n➡️ Sahifa {page_num}/{total_pages} ishlanmoqda...")
            
            if not navigate_to_page(self.driver, page_num, total_pages, self.base_download_path):
                print(f"❌ Sahifa {page_num} ga o'tib bo'lmadi. Jarayon to'xtatilmoqda.")
                break
            
            time.sleep(2) # Kontent to'liq yuklanishi uchun kutish

            # Joriy sahifani qayta ishlash
            filtered_cameras_on_page = process_current_page(self.driver, self.base_download_path, main_window_handle)

            if filtered_cameras_on_page:
                yield filtered_cameras_on_page
            else:
                print(f"ℹ️ Sahifa {page_num} da filtrga mos keladigan kamera topilmadi.")

    except TimeoutException as e:
        print(f"🔥 Kameralar sahifasi yuklanishida vaqt tugadi. Jarayon to'xtatildi. Xato: {e}")
        self._take_screenshot("final_timeout_error.png")
        self._get_page_source("final_timeout_error.html")
    except Exception as e:
        print(f"🔥 Kameralar ma'lumotini olishda kutilmagan xatolik: {e}")
        self._take_screenshot("final_unexpected_error.png")
        self._get_page_source("final_unexpected_error.html")


class TassVisionAutomation:
    """
    TassVision'ni to'liq Selenium yordamida avtomatlashtirish uchun
    Context Manager asosida qurilgan professional klass.
    """
    LOGIN_PAGE_URL = "https://retail.tassvision.ai/auth/login"
    CAMERAS_PAGE_URL = "https://retail.tassvision.ai/counting/support/cameras"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.base_download_path = BASE_DOWNLOAD_PATH
        self.driver: webdriver.Chrome | None = None
        self.current_download_path: Path = self.base_download_path

    def __enter__(self):
        """Context manager'ga kirish: WebDriver'ni sozlash va ishga tushirish."""
        print("🖥️  Selenium WebDriver sozlanmoqda (avtomatik)...")
        options = webdriver.ChromeOptions()
        
        self.prefs = {
            "download.default_directory": str(self.base_download_path),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safeBrowsing.enabled": True 
        }
        options.add_experimental_option("prefs", self.prefs)
        
        try:
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.maximize_window() 
            print(f"📂 Fayllar asosiy '{self.base_download_path}' papkasiga saqlanadi.")
        except WebDriverException as e:
            print(f"🔥 WebDriverni ishga tushirishda xatolik: {e}")
            self.driver = None 
            return None 
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager'dan chiqish: Brauzerni to'g'ri yopish."""
        if self.driver:
            self.driver.quit()
            print("\n👋 Brauzer yopildi.")
        if exc_type:
            print(f"💥 Dastur ishida kutilmagan xatolik yuz berdi: {exc_val}")

    # --- Boshqa modullardan import qilingan funksiyalarni klassga metod sifatida bog'lash ---
    
    # authentication.py dan
    login_with_selenium = login_with_selenium
    
    # export_process.py dan
    _update_download_directory = _update_download_directory
    run_export_process_for_page_cameras = run_export_process_for_page_cameras 
    _wait_for_download_complete = _wait_for_download_complete
    
    # diagnostics.py dan olingan funksiyalarni self bilan ishlaydigan qilib o'rash (wrapping)
    def _take_screenshot(self, filename: str):
        """Drayver mavjudligini tekshirib, skrinshot oladi."""
        if self.driver:
            return take_screenshot(self.driver, self.base_download_path, filename)
        print("❌ WebDriver mavjud emas, skrinshot olib bo'lmadi.")
        
    def _get_page_source(self, filename: str):
        """Drayver mavjudligini tekshirib, sahifa manbasini oladi."""
        if self.driver:
            return get_page_source(self.driver, self.base_download_path, filename)
        print("❌ WebDriver mavjud emas, sahifa manbasini olib bo'lmadi.")

    # Yangi yaratilgan generator funksiyani klassga bog'lash
    get_filtered_cameras_by_page = get_filtered_cameras_generator
