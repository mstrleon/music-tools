#!/usr/bin/env python3
"""
Скрипт для обновления тега Genre в аудио файлах на основе названия папки
Поддерживает форматы: FLAC, MP3, AIFF
"""

import os
import glob
from mutagen import File as MutagenFile
from mutagen.id3 import TCON
from pathlib import Path
import sys

def update_genre_tags(root_directory="."):
    """
    Проходит по всем папкам и обновляет тег Genre в аудио файлах (FLAC, MP3, AIFF)
    на название папки, в которой они находятся
    """
    root_path = Path(root_directory)
    
    if not root_path.exists():
        print(f"❌ Директория {root_directory} не существует!")
        return
    
    print(f"🎵 Начинаю обработку в: {root_path.absolute()}")
    print(f"🔍 Ищу папки и файлы (FLAC, MP3, AIFF)...")
    
    # Счетчики для статистики
    total_files = 0
    updated_files = 0
    errors = 0
    processed_folders = 0
    
    # Поддерживаемые форматы
    AUDIO_EXTENSIONS = ["*.flac", "*.FLAC", "*.mp3", "*.MP3", "*.aiff", "*.AIFF", "*.aif", "*.AIF"]
    
    # Если передана конкретная папка (не текущая директория)
    if root_directory != ".":
        # Обрабатываем только эту папку
        if root_path.is_dir():
            folder_name = root_path.name
            print(f"\n📁 Обрабатываю выбранную папку: {folder_name}")
            print(f"📂 Полный путь: {root_path.absolute()}")
            
            # Ищем все аудио файлы в этой папке
            print(f"🔍 Ищу аудио файлы в папке...")
            audio_files = []
            
            for pattern in AUDIO_EXTENSIONS:
                found_files = list(root_path.glob(pattern))
                audio_files.extend(found_files)
                if found_files:
                    print(f"   🔍 По маске {pattern}: найдено {len(found_files)} файлов")
            
            # Также проверим рекурсивно во вложенных папках
            for pattern in AUDIO_EXTENSIONS:
                found_files = list(root_path.rglob(pattern))
                for f in found_files:
                    if f not in audio_files:
                        audio_files.append(f)
            
            if audio_files:
                print(f"   🔍 Всего найдено рекурсивно: {len(audio_files)} файлов")
            
            if not audio_files:
                print(f"   ❌ Аудио файлы не найдены!")
                print(f"   🔍 Проверяю содержимое папки:")
                all_files = list(root_path.iterdir())
                for item in all_files[:10]:  # показываем первые 10 файлов
                    print(f"      - {item.name} ({'папка' if item.is_dir() else 'файл'})")
                if len(all_files) > 10:
                    print(f"      ... и еще {len(all_files) - 10} элементов")
                return
                
            print(f"   🎧 Найдено {len(audio_files)} аудио файлов")
            processed_folders = 1
            
            # Обрабатываем каждый аудио файл
            for i, audio_file in enumerate(audio_files, 1):
                print(f"\n   🎵 [{i}/{len(audio_files)}] Обрабатываю: {audio_file.name}")
                print(f"      📂 Путь: {audio_file.parent}")
                
                try:
                    total_files += 1
                    
                    # Проверяем размер файла
                    file_size = audio_file.stat().st_size
                    print(f"      📏 Размер файла: {file_size / 1024 / 1024:.1f} MB")
                    
                    # Открываем файл для редактирования метаданных
                    print(f"      🔓 Открываю файл для чтения метаданных...")
                    audio = MutagenFile(str(audio_file))
                    
                    if audio is None:
                        print(f"      ⚠️  Не удалось распознать формат файла")
                        errors += 1
                        continue
                    
                    # Получаем текущий жанр (разные форматы используют разные теги)
                    current_genre = 'НЕТ'
                    if 'GENRE' in audio:
                        genre_value = audio['GENRE']
                        current_genre = str(genre_value[0]) if isinstance(genre_value, list) else str(genre_value)
                    elif hasattr(audio, 'tags') and audio.tags and 'TCON' in audio.tags:
                        # MP3 ID3 тег
                        current_genre = str(audio.tags['TCON'].text[0])
                    
                    # Устанавливаем новый жанр (для MP3 используем TCON frame)
                    if hasattr(audio, 'tags') and hasattr(audio.tags, '__class__') and 'ID3' in audio.tags.__class__.__name__:
                        # MP3 файл с ID3 тегами
                        audio.tags['TCON'] = TCON(encoding=3, text=[folder_name])
                    else:
                        # FLAC, AIFF и другие форматы
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
            
            # Ищем все аудио файлы в текущей папке
            audio_files = []
            for pattern in AUDIO_EXTENSIONS:
                audio_files.extend(list(folder_path.glob(pattern)))
            
            if not audio_files:
                print(f"   ℹ️  Аудио файлы не найдены")
                continue
                
            print(f"   🎧 Найдено {len(audio_files)} аудио файлов")
            
            # Обрабатываем каждый аудио файл
            for i, audio_file in enumerate(audio_files, 1):
                print(f"   🎵 [{i}/{len(audio_files)}] {audio_file.name}")
                
                try:
                    total_files += 1
                    
                    # Открываем файл для редактирования метаданных
                    audio = MutagenFile(str(audio_file))
                    
                    if audio is None:
                        print(f"   ⚠️  Не удалось распознать формат файла")
                        errors += 1
                        continue
                    
                    # Получаем текущий жанр (разные форматы используют разные теги)
                    current_genre = 'НЕТ'
                    if 'GENRE' in audio:
                        genre_value = audio['GENRE']
                        current_genre = str(genre_value[0]) if isinstance(genre_value, list) else str(genre_value)
                    elif hasattr(audio, 'tags') and audio.tags and 'TCON' in audio.tags:
                        # MP3 ID3 тег
                        current_genre = str(audio.tags['TCON'].text[0])
                    
                    # Устанавливаем новый жанр (для MP3 используем TCON frame)
                    if hasattr(audio, 'tags') and hasattr(audio.tags, '__class__') and 'ID3' in audio.tags.__class__.__name__:
                        # MP3 файл с ID3 тегами
                        audio.tags['TCON'] = TCON(encoding=3, text=[folder_name])
                    else:
                        # FLAC, AIFF и другие форматы
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
        print(f"\n⚠️  Убедись что все аудио файлы не заблокированы другими программами")
    
    if total_files == 0:
        print(f"\n🤔 Аудио файлы не найдены. Проверь:")
        print(f"   - Правильно ли выбрана папка")
        print(f"   - Есть ли файлы с расширением .flac, .mp3 или .aiff")
        print(f"   - Доступна ли папка для чтения")

def input_directory():
    """
    Ввод имени директории с проверкой существования
    """
    current_path = Path(".")
    
    while True:
        try:
            print(f"\n📂 Текущая директория: {current_path.absolute()}")
            folder_name = input(f"🎯 Введи имя папки (или '.' для всех папок, 'exit' для выхода): ").strip()
            
            if folder_name.lower() == 'exit':
                print("👋 До свидания!")
                return None
            
            if folder_name == ".":
                return "."  # Все папки
            
            # Проверяем существование папки
            folder_path = current_path / folder_name
            
            if folder_path.exists() and folder_path.is_dir():
                print(f"✅ Выбрана папка: {folder_name}")
                return str(folder_path)
            else:
                print(f"❌ Папка '{folder_name}' не найдена! Попробуй еще раз.")
                
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            return None

def main():
    """
    Главная функция
    """
    print("🎵 Скрипт обновления тегов Genre в аудио файлах")
    print("   Поддерживаемые форматы: FLAC, MP3, AIFF")
    print("=" * 50)
    
    # Если указан аргумент командной строки - используем его
    if len(sys.argv) > 1:
        directory = sys.argv[1]
        print(f"📁 Используется директория из аргумента: {directory}")
    else:
        # Ввод имени папки
        directory = input_directory()
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