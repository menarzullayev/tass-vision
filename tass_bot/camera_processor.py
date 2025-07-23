# tass_bot/camera_processor.py
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pathlib import Path

# Yordamchi funksiyalarni import qilish
from .diagnostics import take_screenshot

def process_current_page(driver: WebDriver, base_download_path: Path, main_window_handle: str) -> list[dict]:
    """
    Joriy sahifadagi kameralarni qayta ishlaydi, filtrlaydi va ma'lumotlarni qaytaradi.
    Filtr: Software version >= 1.85 va < 2.0
    """
    wait = WebDriverWait(driver, 15)
    current_page_cameras = []
    
    rows_xpath = "//div[@class='ant-table-content']//table//tbody/tr[contains(@class, 'ant-table-row')]"
    
    try:
        rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, rows_xpath)))
        print(f"🔗 Sahifada {len(rows)} ta kamera qatori topildi.")
    except TimeoutException:
        print(f"⚠️ Joriy sahifada kamera qatorlari topilmadi. Balki sahifa bo'shdir.")
        take_screenshot(driver, base_download_path, "no_rows_on_page.png")
        return []

    for i, row in enumerate(rows):
        try:
            cols = row.find_elements(By.CSS_SELECTOR, "td.ant-table-cell")
            if len(cols) < 8:
                print(f"⚠️ Qator #{i+1}da kutilgan ustunlar soni (8) topilmadi. O'tkazib yuborilmoqda.")
                continue

            software_version_str = cols[4].text.strip()
            serial_number = cols[2].text.strip()
            
            try:
                software_version_float = float(software_version_str)
                if 1.85 <= software_version_float < 2.0:
                    view_button_link_element = cols[7].find_element(By.CSS_SELECTOR, "a.ant-btn")
                    view_button_link = view_button_link_element.get_attribute("href")
                    camera_id = view_button_link.split('/')[-1] if view_button_link else "N/A"

                    camera_data = {
                        'Organization': cols[0].text.strip(),
                        'Branch': cols[1].text.strip(),
                        'Serial number': serial_number,
                        'Status': cols[3].find_element(By.CSS_SELECTOR, "button span").get_attribute('outerText').strip(),
                        'Software version': software_version_str,
                        'State': cols[5].find_element(By.CSS_SELECTOR, "button span").get_attribute('outerText').strip(),
                        'Latest package': cols[6].text.strip(),
                        '_id': camera_id
                    }
                    current_page_cameras.append(camera_data)
                    print(f"    ✅ Kamera (Serial: {serial_number}, Versiya: {software_version_str}) filtrdan o'tdi.")

                else:
                    # Bu xabar keraksiz loglarni ko'paytirishi mumkin, shuning uchun o'chirib qo'yildi
                    # print(f"    ℹ️ Kamera (Serial: {serial_number}, Versiya: {software_version_str}) versiya shartiga mos kelmadi.")
                    pass

            except ValueError:
                print(f"    ⚠️ Kamera (Serial: {serial_number}) versiyasi '{software_version_str}' son emas. O'tkazib yuborilmoqda.")
        
        except (NoSuchElementException, IndexError) as e:
            print(f"❌ Qator #{i+1} ni ishlashda xatolik: {e}. O'tkazib yuborildi.")
            take_screenshot(driver, base_download_path, f"error_processing_row_{i+1}.png")

    return current_page_cameras
