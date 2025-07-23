import os
from dotenv import load_dotenv
from pathlib import Path

# config va tass_bot/bot_core modullaridan import qilish
from config import BASE_DOWNLOAD_PATH 
from tass_bot.bot_core import TassVisionAutomation 

def main():
    """Asosiy dastur logikasi."""
    load_dotenv()
    login = os.getenv("TASS_LOGIN")
    password = os.getenv("TASS_PASSWORD")

    if not login or not password:
        print("Iltimos, .env faylida TASS_LOGIN va TASS_PASSWORD ni ko'rsating.")
        return

    if not BASE_DOWNLOAD_PATH.exists():
        print(f"📂 Asosiy yuklash uchun '{BASE_DOWNLOAD_PATH}' papkasi yaratilmoqda...")
        BASE_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

    try:
        with TassVisionAutomation(login, password) as bot:
            if bot: 
                if bot.login_with_selenium():
                    total_processed_cameras = 0
                    for cameras_on_page in bot.get_filtered_cameras_by_page():
                        if cameras_on_page:
                            bot.run_export_process_for_page_cameras(cameras_on_page)
                            total_processed_cameras += len(cameras_on_page)
                        else:
                            print("ℹ️ Joriy sahifada filtrlangan kamera topilmadi. Keyingi sahifaga o'tilmoqda.")
                    
                    print(f"\n🎉 Jarayon yakunlandi. Jami {total_processed_cameras} ta kamera ma'lumotlari qayta ishlandi va yuklandi.")
                else:
                    print("Dastur tizimga kira olmadi. Ish davom ettirilmaydi.")
            else:
                print("Dastur WebDriverni ishga tushira olmadi. Ish davom ettirilmaydi.")
    except Exception as e:
        print(f"💥 Dastur ishida kutilmagan umumiy xatolik yuz berdi: {e}")
    finally:
        pass 

if __name__ == "__main__":
    main()
