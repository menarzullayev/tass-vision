# tass_bot/export_process.py
import os
import time
import re
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)


def _update_download_directory(self, new_path: Path):
    """WebDriverning yuklash papkasini dinamik yangilaydi."""
    if self.driver is None:
        print("❌ WebDriver ishga tushmagan, yuklash papkasini yangilash mumkin emas.")
        return

    self.current_download_path = new_path
    if not self.current_download_path.exists():
        print(f"📂 Yangi yuklash papkasi yaratilmoqda: '{self.current_download_path}'")
        self.current_download_path.mkdir(parents=True, exist_ok=True)

    try:
        # CDP (Chrome DevTools Protocol) orqali yuklash papkasini sozlash
        self.driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": str(self.current_download_path),
            },
        )
        print(f"⚙️ Yuklash papkasi '{self.current_download_path}' ga yangilandi.")
    except Exception as e:
        print(f"❌ Yuklash papkasini yangilashda xatolik: {e}")


def _wait_for_download_complete(self, download_folder_path: Path):
    """Berilgan papkada fayl yuklanishini kutadi."""
    download_timeout = 60  # soniya
    start_time = time.time()

    # Jarayonni boshlashdan oldin eski yoki chala yuklangan fayllarni tozalash
    for f in download_folder_path.iterdir():
        if f.suffix == ".crdownload" or f.name.startswith("export"):
            try:
                f.unlink()
                print(f"🧹 Eski yuklash fayli o'chirildi: {f.name}")
            except OSError as e:
                print(
                    f"⚠️ Eski faylni o'chirishda xatolik: {e}. Ehtimol, fayl band bo'lishi mumkin."
                )

    download_completed_file = None

    while time.time() - start_time < download_timeout:
        # .crdownload fayli yo'qligini va .xlsx fayli borligini tekshirish
        xlsx_files = [f for f in download_folder_path.glob("*.xlsx")]
        crdownload_files = [f for f in download_folder_path.glob("*.crdownload")]

        if xlsx_files and not crdownload_files:
            # Eng so'nggi o'zgartirilgan faylni tanlash
            latest_xlsx_file = max(xlsx_files, key=os.path.getmtime)
            # Fayl to'liq yozilganligiga ishonch hosil qilish uchun kichik pauza
            time.sleep(1)
            if latest_xlsx_file.stat().st_size > 0:
                download_completed_file = latest_xlsx_file
                break
        time.sleep(1)

    if download_completed_file:
        print(
            f"✅ Fayl '{download_completed_file.name}' '{download_folder_path.name}' papkasiga muvaffaqiyatli yuklandi."
        )
    else:
        print(
            f"❌ Fayl {download_timeout} soniyada '{download_folder_path.name}' papkasiga yuklanmadi yoki topilmadi."
        )
        self._take_screenshot(f"download_timeout_{download_folder_path.name}.png")


def run_export_process_for_page_cameras(self, cameras_on_page: list):
    """
    Berilgan sahifadagi kameralar ro'yxati uchun export jarayonini bajaradi.
    Har bir kamera yangi tabda ochiladi, bu asosiy sahifadagi paginationni saqlab qoladi.
    """
    if not self.driver:
        print("❌ WebDriver ishga tushmagan. Jarayon to'xtatildi.")
        return
    if not cameras_on_page:
        print("ℹ️ Joriy sahifada export qilinadigan kameralar topilmadi.")
        return

    # Asosiy kamera ro'yxati sahifasining oynasini (handle) eslab qolish
    main_window_handle = self.driver.current_window_handle

    print(
        f"\n⏳ Joriy sahifadagi {len(cameras_on_page)} ta kamera uchun avtomatlashtirish boshlandi..."
    )
    for camera in cameras_on_page:
        camera_id = camera["_id"]
        serial_number = camera.get("Serial number", camera_id)
        serial_number_safe = re.sub(r'[\\/:*?"<>|]', "_", serial_number)

        camera_download_folder = self.base_download_path / serial_number_safe
        self._update_download_directory(camera_download_folder)

        print(f"\n--- Ishlanmoqda: Kamera {serial_number_safe} (ID: {camera_id}) ---")

        new_tab_handle = None
        try:
            camera_detail_url = (
                f"https://retail.tassvision.ai/counting/support/cameras/{camera_id}"
            )

            # 1. YANGI TAB OCHISH VA UNGA O'TISH
            self.driver.execute_script(
                "window.open(arguments[0], '_blank');", camera_detail_url
            )

            # Yangi ochilgan tabni topish
            all_handles = self.driver.window_handles
            new_tab_handle = [h for h in all_handles if h != main_window_handle][0]
            self.driver.switch_to.window(new_tab_handle)
            print(f"➡️ Yangi tabda kamera sahifasi ochildi: {self.driver.current_url}")

            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.url_to_be(camera_detail_url))

            # 2. "Логирование" BO'LIMINI TOPISH VA BOSISH
            log_tab_xpath = "//div[contains(@class, 'ant-tabs-tab') and (.//text()[normalize-space()='Логирование'] or .//text()[normalize-space()='Loggings'])]"
            log_tab = wait.until(EC.presence_of_element_located((By.XPATH, log_tab_xpath)))

            if "ant-tabs-tab-active" not in log_tab.get_attribute("class"):
                try:
                    log_tab.click()
                    print("🖱️ 'Логирование' bo'limiga o'tildi.")
                except ElementClickInterceptedException:
                    print(
                        "⚠️ 'Логирование' tugmasi boshqa element tomonidan to'silgan. JavaScript orqali bosilmoqda."
                    )
                    self.driver.execute_script("arguments[0].click();", log_tab)
            else:
                print("ℹ️ 'Логирование' bo'limi allaqachon faol.")

            # Tab bosilgandan keyin kontent yangilanishini kutish
            export_btn_xpath = "//button[.//span[normalize-space()='Экспорт'] or .//span[normalize-space()='Export']]"
            wait.until(EC.element_to_be_clickable((By.XPATH, export_btn_xpath)))
            time.sleep(1)  # Barqarorlik uchun qo'shimcha kutish

            # 3. "Экспорт" TUGMASINI BOSISH
            export_button = self.driver.find_element(By.XPATH, export_btn_xpath)
            export_button.click()
            print("🖱️ 'Экспорт' tugmasi bosildi. Fayl yuklanishi kutilmoqda...")

            # 4. FAYL YUKLANISHINI KUTISH
            self._wait_for_download_complete(camera_download_folder)

        except (TimeoutException, NoSuchElementException) as e:
            print(
                f"❌ '{serial_number_safe}' kamerasini ishlashda xatolik: Sahifa elementi topilmadi yoki vaqt tugadi. {e}"
            )
            self._take_screenshot(f"error_{serial_number_safe}.png")
        except Exception as e:
            print(f"❌ '{serial_number_safe}' kamerasini ishlashda kutilmagan xatolik: {e}")
            self._take_screenshot(f"error_unexpected_{serial_number_safe}.png")
        finally:
            # 5. JARAYON TUGAGACH (XATOLIK BO'LSA HAM) YANGI TABNI YOPISH
            if new_tab_handle and new_tab_handle in self.driver.window_handles:
                self.driver.close()
            # Asosiy oynaga qaytish
            self.driver.switch_to.window(main_window_handle)
            print("↩️ Asosiy sahifaga qaytildi.")

    print(f"\n✅ Joriy sahifadagi kameralarni ishlash yakunlandi.")