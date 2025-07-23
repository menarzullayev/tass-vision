# retail_automation/tass_bot/authentication.py

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# TassVisionAutomation klassining Login_PAGE_URL ni bilishi kerak, bu config orqali bo'ladi

def login_with_selenium(self):
    """Selenium orqali to'g'ridan-to'g'ri tizimga kirish."""
    if not self.driver: 
        return False
    
    try:
        print(f"🔑 '{self.username}' logini bilan tizimga kirilmoqda...")
        self.driver.get(self.LOGIN_PAGE_URL)
        wait = WebDriverWait(self.driver, 20)
        
        login_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="login"]')))
        login_input.send_keys(self.username)
        
        password_input = self.driver.find_element(By.CSS_SELECTOR, 'input[formcontrolname="password"]')
        password_input.send_keys(self.password)
        
        time.sleep(1)

        signin_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.login-form-button')))
        signin_button.click()

        wait.until(EC.url_contains('/personal'))
        
        print("✅ Tizimga muvaffaqiyatli kirildi va '/personal' sahifasiga o'tildi!")
        return True
    except TimeoutException:
        print("🔥 Login qilishda xatolik: Kutilgan sahifa 20 soniyada ochilmadi. Login/parol xato yoki internet sekin bo'lishi mumkin.")
        return False
    except NoSuchElementException as e:
        print(f"🔥 Login elementlari topilmadi: {e}. Sahifa tuzilishi o'zgargan bo'lishi mumkin.")
        return False
    except Exception as e:
        print(f"🔥 Selenium orqali login qilishda noma'lum xatolik: {e}")
        return False

