# tass_bot/page_navigator.py
import time
import re
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)

# Yordamchi funksiyalarni import qilish
from .diagnostics import take_screenshot


def get_total_pages(driver: WebDriver, base_download_path: Path) -> int:
    """
    Kameradagi jami sahifalar sonini aniqlaydi.
    Bu funksiya pagination elementlaridan ma'lumotlarni oladi.
    """
    total_pages = 1
    items_per_page = 10

    try:
        wait = WebDriverWait(driver, 10)

        # Har bir sahifadagi elementlar sonini olish
        per_page_select = wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "nz-select.ant-pagination-options-size-changer .ant-select-selection-item",
                )
            )
        )
        per_page_text = per_page_select.get_attribute("title")
        if per_page_text:
            match_per_page = re.search(r"(\d+)\s*/\s*(?:page|стр\.)", per_page_text)
            if match_per_page:
                items_per_page = int(match_per_page.group(1))

        # Jami natijalar va sahifalar sonini olish
        total_results_text_xpath = "//li[contains(@class, 'ant-pagination-total-text')]"
        total_results_element = wait.until(
            EC.presence_of_element_located((By.XPATH, total_results_text_xpath))
        )
        total_results_text = total_results_element.text

        match_total_items = re.search(
            r"(?:of|из)\s*(\d+)\s*(?:results|результатов)", total_results_text
        )
        if match_total_items:
            total_items = int(match_total_items.group(1))
            total_pages = (total_items + items_per_page - 1) // items_per_page
            print(
                f"📊 Jami {total_items} ta natija topildi. {items_per_page} ta element/sahifa bilan {total_pages} ta sahifa mavjud."
            )
        else:
            print(
                f"⚠️ Jami natijalar sonini aniqlashda muammo: '{total_results_text}'. Standart: {total_pages} sahifa."
            )

    except (TimeoutException, NoSuchElementException) as e:
        print(f"❌ Sahifalar sonini aniqlashda xatolik: {e}. Standart qiymat 1 ishlatiladi.")
        take_screenshot(driver, base_download_path, "error_get_total_pages.png")

    time.sleep(1)
    return total_pages


def navigate_to_page(
    driver: WebDriver, page_num: int, total_pages: int, base_download_path: Path
) -> bool:
    """
    Belgilangan sahifa raqamiga o'tadi. Muvaffaqiyatli bo'lsa True, aks holda False qaytaradi.
    """
    wait = WebDriverWait(driver, 20)

    # Birinchi sahifadan boshqa har qanday sahifa uchun joriy faol sahifani tekshirish
    if page_num > 1:
        try:
            active_page_element = driver.find_element(
                By.XPATH, "//li[contains(@class, 'ant-pagination-item-active')]"
            )
            # --- XATOLIK TUZATILDI ---
            # 'title' atributi None bo'lishi mumkin, shuning uchun tekshiruv qo'shildi
            title_attr = active_page_element.get_attribute("title")
            if title_attr and title_attr.isdigit():
                active_page_num = int(title_attr)
                if active_page_num == page_num:
                    print(f"ℹ️ Sahifa {page_num} allaqachon faol.")
                    return True
        except (NoSuchElementException, ValueError):
            # Agar faol sahifa topilmasa yoki 'title' atributida raqam bo'lmasa, davom etamiz
            pass

    # Sahifaga o'tish (raqamli tugma orqali)
    for attempt in range(5):
        try:
            page_button_xpath = (
                f"//li[@title='{page_num}' and contains(@class, 'ant-pagination-item')]"
            )
            page_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, page_button_xpath))
            )

            print(f"🖱️ {page_num}-sahifaga o'tishga urinish {attempt+1}...")
            driver.execute_script("arguments[0].click();", page_button)

            # Yangi sahifaning faol bo'lishini kutish
            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element(
                    (By.XPATH, "//li[contains(@class, 'ant-pagination-item-active')]"),
                    str(page_num),
                )
            )
            print(f"✅ {page_num}-sahifaga muvaffaqiyatli o'tildi.")

            # Jadval yangilanishini kutish
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//div[@class='ant-table-content']//table//tbody/tr[contains(@class, 'ant-table-row')]",
                    )
                )
            )
            return True  # Muvaffaqiyatli o'tildi
        except (
            StaleElementReferenceException,
            TimeoutException,
            NoSuchElementException,
        ) as e:
            print(
                f"🔄 Sahifa {page_num} tugmasini topish/bosishda xato ({type(e).__name__}). {attempt+1}/{5} urinish. Qayta urinish..."
            )
            time.sleep(2 + attempt)
            if attempt == 4:
                print(f"❌ Sahifa {page_num} ga o'tishda doimiy xato. Jarayon to'xtatildi.")
                take_screenshot(
                    driver, base_download_path, f"error_navigate_page_{page_num}.png"
                )
                return False
    return False
