import os
import shutil
from pathlib import Path

# 1. Yuklangan loglar papkasi
SOURCE_DIRECTORY = Path(r"D:\nsn\Downloads")

# 2. Barcha loglar uchun
DESTINATION_DIRECTORY = Path(r"E:\logs")



def collect_and_rename_logs():
    """
    Manba papkasidagi har bir ichki jilddan .xlsx faylini topadi,
    uni jild nomi bilan qayta nomlaydi va yakuniy papkaga ko'chiradi.
    """
    if not SOURCE_DIRECTORY.exists():
        print(f"❌ XATOLIK: Manba papkasi topilmadi: {SOURCE_DIRECTORY}")
        return

    try:
        DESTINATION_DIRECTORY.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return

    processed_files_count = 0
    
    for item in SOURCE_DIRECTORY.iterdir():
        if item.is_dir():
            camera_folder_path = item
            camera_serial_number = item.name 

            try:
                xlsx_files = list(camera_folder_path.glob("*.xlsx"))

                if not xlsx_files:
                    print(f"⚠️ '{camera_serial_number}' papkasida .xlsx fayl topilmadi.")
                    continue

                original_file_path = xlsx_files[0]

                new_file_name = f"{camera_serial_number}.xlsx"
                destination_file_path = DESTINATION_DIRECTORY / new_file_name

                shutil.move(original_file_path, destination_file_path)
                
                print(f"✅ Ko'chirildi: '{original_file_path.name}' -> '{new_file_name}'")
                processed_files_count += 1

            except IndexError:
                print(f"⚠️ '{camera_serial_number}' papkasida .xlsx fayl topilmadi (IndexError).")
            except Exception as e:
                print(f"❌ XATOLIK: '{camera_serial_number}' papkasida muammo: {e}")

    print(f"\n🎉 Jarayon yakunlandi! Jami {processed_files_count} ta fayl qayta ishlandi.")


if __name__ == "__main__":
    collect_and_rename_logs()
