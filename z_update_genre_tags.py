#!/usr/bin/env python3
"""
Скрипт для обновления тега Genre в FLAC файлах на основе названия папки
"""

import os
import glob
from mutagen.flac import FLAC
from pathlib import Path
import sys

def update_genre_tags(root_directory="."):
    """
    Проходит по всем папкам и обновляет тег Genre в FLAC файлах
    на название папки, в которой они находятся
    """
    root_path = Path(root_directory)
    
    if not root_path.exists():
        print(f"❌ Директория {root_directory} не существует!")
        return
    
    print(f"🎵 Начинаю обработку в: {root_path.absolute()}")
    print(f"🔍 Ищу папки и файлы...")
    
    # Счетчики для статистики
    total_files = 0
    updated_files = 0
    errors = 0
    processed_folders = 0
    
    # Если передана конкретная папка (не текущая директория)
    if root_directory != ".":
        # Обрабатываем только эту папку
        if root_path.is_dir():
            folder_name = root_path.name
            print(f"\n📁 Обрабатываю выбранную папку: {folder_name}")
            print(f"📂 Полный путь: {root_path.absolute()}")
            
            # Ищем все FLAC файлы в этой папке
            print(f"🔍 Ищу FLAC файлы в папке...")
            flac_patterns = ["*.flac", "*.FLAC"]
            flac_files = []
            
            for pattern in flac_patterns:
                found_files = list(root_path.glob(pattern))
                flac_files.extend(found_files)
                print(f"   🔍 По маске {pattern}: найдено {len(found_files)} файлов")
            
            # Также проверим рекурсивно во вложенных папках
            for pattern in flac_patterns:
                found_files = list(root_path.rglob(pattern))
                for f in found_files:
                    if f not in flac_files:
                        flac_files.append(f)
                print(f"   🔍 Рекурсивно по маске {pattern}: всего найдено {len(list(root_path.rglob(pattern)))} файлов")
            
            if not flac_files:
                print(f"   ❌ FLAC файлы не найдены!")
                print(f"   🔍 Проверяю содержимое папки:")
                all_files = list(root_path.iterdir())
                for item in all_files[:10]:  # показываем первые 10 файлов
                    print(f"      - {item.name} ({'папка' if item.is_dir() else 'файл'})")
                if len(all_files) > 10:
                    print(f"      ... и еще {len(all_files) - 10} элементов")
                return
                
            print(f"   🎧 Найдено {len(flac_files)} FLAC файлов")
            processed_folders = 1
            
            # Обрабатываем каждый FLAC файл
            for i, flac_file in enumerate(flac_files, 1):
                print(f"\n   🎵 [{i}/{len(flac_files)}] Обрабатываю: {flac_file.name}")
                print(f"      📂 Путь: {flac_file.parent}")
                
                try:
                    total_files += 1
                    
                    # Проверяем размер файла
                    file_size = flac_file.stat().st_size
                    print(f"      📏 Размер файла: {file_size / 1024 / 1024:.1f} MB")
                    
                    # Открываем файл для редактирования метаданных
                    print(f"      🔓 Открываю файл для чтения метаданных...")
                    audio = FLAC(str(flac_file))
                    
                    # Получаем текущий жанр
                    current_genre = audio.get('GENRE', [''])[0] if 'GENRE' in audio else 'НЕТ'
                    
                    # Устанавливаем новый жанр
                    audio['GENRE'] = folder_name
                    
                    # Сохраняем изменения
                    audio.save()
                    
                    updated_files += 1
                    print(f"      ✅ Жанр: было '{current_genre}' - стало '{folder_name}'")
                    
                except Exception as e:
                    errors += 1
                    print(f"      ❌ ОШИБКА: {str(e)}")
                    import traceback
                    print(f"      🐛 Детали ошибки: {traceback.format_exc()}")
        else:
            print(f"❌ {root_directory} не является папкой!")
            return
    else:
        # Обрабатываем все поддиректории в текущей папке
        print(f"🔍 Сканирую поддиректории...")
        folders = [folder for folder in root_path.iterdir() if folder.is_dir()]
        print(f"📁 Найдено папок: {len(folders)}")
        
        for folder_path in folders:
            folder_name = folder_path.name
            print(f"\n📁 Обрабатываю папку: {folder_name}")
            processed_folders += 1
            
            # Ищем все FLAC файлы в текущей папке
            flac_files = list(folder_path.glob("*.flac")) + list(folder_path.glob("*.FLAC"))
            
            if not flac_files:
                print(f"   ℹ️  FLAC файлы не найдены")
                continue
                
            print(f"   🎧 Найдено {len(flac_files)} FLAC файлов")
            
            # Обрабатываем каждый FLAC файл
            for i, flac_file in enumerate(flac_files, 1):
                print(f"   🎵 [{i}/{len(flac_files)}] {flac_file.name}")
                
                try:
                    total_files += 1
                    
                    # Открываем файл для редактирования метаданных
                    audio = FLAC(str(flac_file))
                    
                    # Получаем текущий жанр
                    current_genre = audio.get('GENRE', [''])[0] if 'GENRE' in audio else 'НЕТ'
                    
                    # Устанавливаем новый жанр
                    audio['GENRE'] = folder_name
                    
                    # Сохраняем изменения
                    audio.save()
                    
                    updated_files += 1
                    print(f"   ✅ Жанр: было '{current_genre}' - стало '{folder_name}'")
                    
                except Exception as e:
                    errors += 1
                    print(f"   ❌ Ошибка: {str(e)}")
    
    # Выводим статистику
    print(f"\n" + "="*60)
    print(f"📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
    print(f"   📁 Обработано папок: {processed_folders}")
    print(f"   🎵 Всего файлов найдено: {total_files}")
    print(f"   ✅ Успешно обновлено: {updated_files}")
    print(f"   ❌ Ошибок: {errors}")
    print(f"="*60)
    
    if errors > 0:
        print(f"\n⚠️  Убедись что все FLAC файлы не заблокированы другими программами")
    
    if total_files == 0:
        print(f"\n🤔 FLAC файлы не найдены. Проверь:")
        print(f"   - Правильно ли выбрана папка")
        print(f"   - Есть ли файлы с расширением .flac или .FLAC")
        print(f"   - Доступна ли папка для чтения")

def select_directory():
    """
    Интерактивный выбор директории
    """
    current_path = Path(".")
    
    print(f"\n📂 Доступные папки в: {current_path.absolute()}")
    print("-" * 50)
    
    # Получаем список всех папок
    folders = [folder for folder in current_path.iterdir() if folder.is_dir()]
    
    if not folders:
        print("❌ Папки не найдены!")
        return None
    
    # Показываем список папок с номерами
    for i, folder in enumerate(folders, 1):
        print(f"{i:2d}. {folder.name}")
    
    print(f"{len(folders)+1:2d}. Все папки (текущая директория)")
    print(f" 0. Выход")
    
    while True:
        try:
            choice = input(f"\n🎯 Выбери папку (1-{len(folders)+1}, 0 для выхода): ").strip()
            
            if choice == "0":
                print("👋 До свидания!")
                return None
            
            choice_num = int(choice)
            
            if choice_num == len(folders) + 1:
                return "."  # Все папки
            elif 1 <= choice_num <= len(folders):
                selected_folder = folders[choice_num - 1]
                print(f"✅ Выбрана папка: {selected_folder.name}")
                return str(selected_folder)
            else:
                print(f"❌ Неверный выбор! Введи число от 0 до {len(folders)+1}")
                
        except ValueError:
            print("❌ Введи корректное число!")
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            return None

def main():
    """
    Главная функция
    """
    print("🎵 Скрипт обновления тегов Genre в FLAC файлах")
    print("=" * 50)
    
    # Если указан аргумент командной строки - используем его
    if len(sys.argv) > 1:
        directory = sys.argv[1]
        print(f"📁 Используется директория из аргумента: {directory}")
    else:
        # Интерактивный выбор папки
        directory = select_directory()
        if directory is None:
            return
    
    try:
        update_genre_tags(directory)
    except KeyboardInterrupt:
        print("\n\n⏹️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")

if __name__ == "__main__":
    main() 