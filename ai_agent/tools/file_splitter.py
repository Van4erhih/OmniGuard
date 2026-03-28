import os
from typing import List, Tuple

TELEGRAM_FILE_LIMIT = 50 * 1024 * 1024  # 50 MB (безопасный лимит для Telegram)

class FileSplitter:
    """Разбивка больших файлов на части для отправки в Telegram"""
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Получить размер файла в байтах"""
        return os.path.getsize(filepath)
    
    @staticmethod
    def needs_split(filepath: str) -> bool:
        """Проверить нужно ли разбивать файл"""
        return FileSplitter.get_file_size(filepath) > TELEGRAM_FILE_LIMIT
    
    @staticmethod
    def split_file(filepath: str, output_dir: str = "split_files") -> Tuple[bool, List[str]]:
        """Разбить файл на части
        
        Args:
            filepath: путь к файлу
            output_dir: папка для сохранения частей
        
        Returns:
            (success, list_of_part_paths)
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            file_size = FileSplitter.get_file_size(filepath)
            
            if file_size <= TELEGRAM_FILE_LIMIT:
                return True, [filepath]
            
            # Вычислить количество частей
            num_parts = (file_size + TELEGRAM_FILE_LIMIT - 1) // TELEGRAM_FILE_LIMIT
            chunk_size = (file_size + num_parts - 1) // num_parts
            
            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(filename)
            
            part_paths = []
            
            with open(filepath, 'rb') as f:
                for part_num in range(1, num_parts + 1):
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    part_filename = f"{name}_part{part_num}of{num_parts}{ext}"
                    part_path = os.path.join(output_dir, part_filename)
                    
                    with open(part_path, 'wb') as part_file:
                        part_file.write(chunk)
                    
                    part_paths.append(part_path)
            
            return True, part_paths
        
        except Exception as e:
            print(f"File splitting error: {e}")
            return False, []
    
    @staticmethod
    def get_split_message(num_parts: int, original_filename: str) -> str:
        """Получить сообщение о разбивке файла"""
        return (
            f"⚠️ Файл '{original_filename}' слишком большой для отправки в Telegram.\n\n"
            f"Я разделил его на {num_parts} частей:\n"
            f"• Часть 1 из {num_parts}\n"
            f"• Часть 2 из {num_parts}\n"
            f"...\n\n"
            f"После получения всех частей:\n"
            f"1. Откройте папку с файлами\n"
            f"2. Выделите все части (part1, part2...)\n"
            f"3. Объедините их в одном файле (скопируйте содержимое по порядку)\n\n"
            f"Или используйте команду (Windows):\n"
            f"`copy /B part1.xlsx + part2.xlsx + ... result.xlsx`\n\n"
            f"Начинаю отправку файлов..."
        )
    
    @staticmethod
    def get_assembly_instructions(num_parts: int, original_filename: str) -> str:
        """Получить инструкции по сборке файла"""
        name, ext = os.path.splitext(original_filename)
        
        windows_cmd = f"copy /B {name}_part1of{num_parts}{ext}"
        for i in range(2, num_parts + 1):
            windows_cmd += f" + {name}_part{i}of{num_parts}{ext}"
        windows_cmd += f" {name}_final{ext}"
        
        return (
            f"📋 Инструкции по сборке файла\n\n"
            f"Вы получили {num_parts} частей файла '{original_filename}'\n\n"
            f"**Способ 1 (Windows - через командную строку):**\n"
            f"`{windows_cmd}`\n\n"
            f"**Способ 2 (Любая ОС - WinRAR/7-Zip):**\n"
            f"1. Выделите все части part1, part2 и т.д.\n"
            f"2. Кликните правой кнопкой → Объединить\n\n"
            f"**Способ 3 (Python):**\n"
            f"```python\n"
            f"with open('{name}_final{ext}', 'wb') as outfile:\n"
            f"    for i in range(1, {num_parts + 1}):\n"
            f"        with open('{name}_part{{i}}of{num_parts}{ext}', 'rb') as part:\n"
            f"            outfile.write(part.read())\n"
            f"```"
        )
