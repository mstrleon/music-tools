#!/usr/bin/env python3
"""
Скрипт для перемещения аудиофайлов в папки по жанрам
Читает тег GENRE из файлов и перемещает их в соответствующие подпапки
Поддерживает: FLAC, MP3, MP4, OGG, OPUS, AIFF
При создании новой папки предлагает выбор из похожих существующих папок
"""

import os
import shutil
from pathlib import Path
import sys
from mutagen import File as MutagenFile
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from mutagen.aiff import AIFF
from mutagen.id3 import TCON
import re
import signal
import subprocess
import platform
import threading
import time
import select

# Глобальная переменная для отслеживания прерывания
interrupted = False

def signal_handler(sig, frame):
    """Обработчик сигнала прерывания"""
    global interrupted
    interrupted = True
    print("\n\n⏹️  Получен сигнал прерывания. Завершение работы...")
    sys.exit(0)

def check_exit(input_str):
    """Проверяет, хочет ли пользователь выйти"""
    if input_str.lower() in ['q', 'quit', 'exit', 'выход', '0']:
        print("👋 До свидания!")
        sys.exit(0)
    return False

def safe_input(prompt):
    """Безопасный ввод с возможностью выхода"""
    try:
        user_input = input(prompt).strip()
        check_exit(user_input)
        return user_input
    except KeyboardInterrupt:
        print("\n\n⏹️  Прервано пользователем")
        sys.exit(0)

def play_audio_file(file_path, background=False):
    """
    Воспроизводит аудиофайл в командной строке
    """
    try:
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            if background:
                subprocess.Popen(["afplay", str(file_path)], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["afplay", str(file_path)], check=True)
        elif system == "linux":
            # Пробуем разные плееры для Linux
            players = ["mpv", "mplayer", "vlc", "paplay"]
            for player in players:
                try:
                    if background:
                        subprocess.Popen([player, str(file_path)], 
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        subprocess.run([player, str(file_path)], check=True, 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            else:
                print("   ❌ ⚠️  Не найден подходящий аудиоплеер для Linux")
                return False
        elif system == "windows":
            # Windows
            if background:
                subprocess.Popen(["start", str(file_path)], shell=True, 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["start", str(file_path)], shell=True, check=True)
        else:
            print(f"   ❌ ⚠️  Неподдерживаемая операционная система: {system}")
            return False
            
        return True
        
    except subprocess.CalledProcessError:
        print("   ❌ ⚠️  Ошибка воспроизведения файла")
        return False
    except Exception as e:
        print(f"   ❌ ⚠️  Ошибка: {str(e)}")
        return False

def play_audio_with_interrupt(file_path):
    """
    Воспроизводит аудиофайл с возможностью прерывания по нажатию клавиши
    Начинает с 1-й минуты (пропускает первые 60 секунд)
    """
    try:
        system = platform.system().lower()
        
        # Используем ffplay для всех систем - он поддерживает -ss для пропуска времени
        cmd = ["ffplay", "-ss", "60", "-nodisp", "-autoexit", str(file_path)]
        
        # Запускаем процесс
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("   (нажмите любую клавишу для остановки)")
        
        # Ждем завершения процесса или нажатия клавиши
        while process.poll() is None:
            try:
                # Проверяем, есть ли ввод от пользователя
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    input()  # Читаем ввод
                    # Сразу принудительно завершаем ffplay
                    process.terminate()
                    try:
                        process.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
            except:
                # Если select не работает, используем простую проверку
                try:
                    import msvcrt
                    if msvcrt.kbhit():
                        msvcrt.getch()
                        # Сразу принудительно завершаем ffplay
                        process.terminate()
                        try:
                            process.wait(timeout=0.5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        break
                except:
                    pass
            time.sleep(0.1)
        
        # Останавливаем процесс
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    # Принудительное завершение через pkill для ffplay
                    if system in ["darwin", "linux"]:
                        try:
                            subprocess.run(["pkill", "-f", "ffplay"], 
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except:
                            pass
                    elif system == "windows":
                        try:
                            subprocess.run(["taskkill", "/F", "/IM", "ffplay.exe"], 
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except:
                            pass
        
        print("   ⏹️  Воспроизведение остановлено")
        return True
        
    except Exception as e:
        print(f"   ❌ ⚠️  Ошибка: {str(e)}")
        return False

def open_audio_file(file_path):
    """
    Открывает аудиофайл в системном плеере по умолчанию
    """
    try:
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            subprocess.run(["open", str(file_path)], check=True)
        elif system == "linux":
            subprocess.run(["xdg-open", str(file_path)], check=True)
        elif system == "windows":
            subprocess.run(["start", str(file_path)], shell=True, check=True)
        else:
            print(f"   ❌ ⚠️  Неподдерживаемая операционная система: {system}")
            return False
            
        return True
        
    except subprocess.CalledProcessError:
        print("   ❌ ⚠️  Ошибка открытия файла")
        return False
    except Exception as e:
        print(f"   ❌ ⚠️  Ошибка: {str(e)}")
        return False

def play_audio_and_return(audio_file):
    """
    Воспроизводит трек и сразу возвращается к выбору папки
    """
    print(f"\n🎵 ▶️  Воспроизведение трека: {audio_file.name}")
    if not play_audio_with_interrupt(audio_file):
        print("❌ Ошибка воспроизведения")
    return 'back'

def debug_mp3_tags(file_path):
    """
    Отладочная функция для просмотра всех тегов в MP3 файле
    """
    try:
        audio = MP3(str(file_path))
        print(f"      🔍 Доступные теги в {file_path.name}:")
        for key, value in audio.items():
            print(f"         {key}: {value}")
        return True
    except Exception as e:
        print(f"      ❌ Ошибка чтения тегов: {str(e)}")
        return False

def get_genre_from_file(file_path):
    """
    Извлекает жанр из аудиофайла
    Поддерживает: FLAC, MP3, MP4, OGG, OPUS, AIFF
    """
    try:
        # Определяем тип файла по расширению
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.flac':
            audio = FLAC(str(file_path))
        elif file_ext == '.mp3':
            audio = MP3(str(file_path))
        elif file_ext in ['.m4a', '.mp4']:
            audio = MP4(str(file_path))
        elif file_ext == '.ogg':
            # Пробуем определить тип OGG файла
            try:
                audio = OggVorbis(str(file_path))
            except:
                audio = OggOpus(str(file_path))
        elif file_ext == '.opus':
            audio = OggOpus(str(file_path))
        elif file_ext == '.aiff':
            audio = AIFF(str(file_path))
        else:
            # Пробуем универсальный метод
            audio = MutagenFile(str(file_path))
        
        if audio is None:
            return None
            
        # Получаем жанр - для MP3 пробуем разные теги
        genre = None
        
        if file_ext == '.mp3':
            # Для MP3 пробуем разные варианты тегов жанра
            genre_tags = ['TCON', 'GENRE', 'Genre', 'genre']
            for tag in genre_tags:
                if tag in audio:
                    genre_value = audio[tag]
                    print(f"      🔍 Найден тег {tag}: {genre_value} (тип: {type(genre_value)})")
                    
                    # Обрабатываем разные типы значений
                    if isinstance(genre_value, list) and len(genre_value) > 0:
                        genre = str(genre_value[0])
                    elif isinstance(genre_value, str):
                        genre = genre_value
                    elif hasattr(genre_value, 'text'):
                        # Для некоторых объектов mutagen
                        genre = str(genre_value.text[0]) if genre_value.text else str(genre_value)
                    else:
                        # Пробуем преобразовать в строку
                        genre = str(genre_value)
                    
                    if genre:
                        print(f"      ✅ Извлечен жанр: '{genre}'")
                        break
            
            # Если жанр не найден, показываем отладочную информацию
            if not genre:
                print(f"      ⚠️  Жанр не найден в MP3 файле")
                debug_mp3_tags(file_path)
        else:
            # Для других форматов используем стандартный GENRE
            if 'GENRE' in audio:
                genre_value = audio['GENRE']
                if isinstance(genre_value, list) and len(genre_value) > 0:
                    genre = str(genre_value[0])
                elif isinstance(genre_value, str):
                    genre = genre_value
        
        # Очищаем жанр от лишних символов
        if genre:
            # Сначала обрезаем по символу '/' и берем только первую часть
            genre = genre.split('/')[0].strip()
            
            # Убираем другие недопустимые символы для имен папок
            genre = re.sub(r'[<>:"\\|?*]', '_', genre.strip())
            genre = re.sub(r'\s+', ' ', genre)  # Убираем лишние пробелы
            
        return genre if genre else None
        
    except Exception as e:
        print(f"      ❌ Ошибка чтения метаданных: {str(e)}")
        return None

def find_similar_folders(base_path, genre):
    """
    Ищет похожие существующие папки
    """
    existing_folders = [folder.name for folder in base_path.iterdir() if folder.is_dir()]
    similar_folders = []
    
    # Простой поиск по частичному совпадению
    genre_lower = genre.lower()
    for folder in existing_folders:
        folder_lower = folder.lower()
        if genre_lower in folder_lower or folder_lower in genre_lower:
            similar_folders.append(folder)
    
    return similar_folders

def get_folder_name_from_user(base_path, genre, audio_file=None):
    """
    Упрощенный процесс получения названия папки от пользователя
    Если папка не найдена - сразу запускает трек
    """
    # Ищем похожие папки
    similar_folders = find_similar_folders(base_path, genre)
    
    if similar_folders:
        print(f"\n🔍 Найдена папка для жанра '{genre}': {similar_folders[0]}")
        if audio_file:
            print(f"🎵 Трек: {audio_file.name}")
            print(f"🎵 ▶️  Запускаю трек...")
            play_audio_with_interrupt(audio_file)
        
        # Просто запрашиваем название папки с дефолтом
        default_folder = f"_{genre}"
        folder_name = safe_input(f"\n✏️  Введите папку которую создать ({default_folder}): ").strip()
        
        if not folder_name:
            folder_name = default_folder
        
        return folder_name
    else:
        print(f"\n📁 Папка для жанра '{genre}' не найдена")
        if audio_file:
            print(f"🎵 Трек: {audio_file.name}")
            print(f"🎵 ▶️  Запускаю трек...")
            play_audio_with_interrupt(audio_file)
        
        # Просто запрашиваем название папки с дефолтом
        default_folder = f"_{genre}"
        folder_name = safe_input(f"\n✏️  Введите папку которую создать ({default_folder}): ").strip()
        
        if not folder_name:
            folder_name = default_folder
        
        return folder_name

def create_genre_folder(base_path, genre, audio_file=None):
    """
    Создает папку для жанра с упрощенным процессом
    Возвращает (genre_folder, new_genre_name, is_custom, was_created)
    """
    # Сначала проверяем, существует ли уже папка с таким именем
    genre_folder = base_path / genre
    if genre_folder.exists():
        print(f"   ✅ Найдена папка: {genre}")
        return genre_folder, genre, False, False
    
    # Если папки нет, спрашиваем пользователя
    folder_name = get_folder_name_from_user(base_path, genre, audio_file)
    genre_folder = base_path / folder_name
    
    try:
        was_created = False
        if genre_folder.exists():
            print(f"   ✅ Найдена папка: {folder_name}")
        else:
            genre_folder.mkdir(exist_ok=True)
            print(f"   ✅ Создана папка: {folder_name}")
            was_created = True
        
        # Определяем, было ли выбрано кастомное имя
        is_custom = folder_name != genre and not folder_name.startswith('_')
        return genre_folder, folder_name, is_custom, was_created
    except Exception as e:
        print(f"      ❌ Ошибка создания папки {folder_name}: {str(e)}")
        return None, None, False, False

def update_genre_in_file(file_path, new_genre):
    """
    Обновляет жанр в аудиофайле
    """
    try:
        # Определяем тип файла по расширению
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.flac':
            audio = FLAC(str(file_path))
        elif file_ext == '.mp3':
            audio = MP3(str(file_path))
        elif file_ext in ['.m4a', '.mp4']:
            audio = MP4(str(file_path))
        elif file_ext == '.ogg':
            try:
                audio = OggVorbis(str(file_path))
            except:
                audio = OggOpus(str(file_path))
        elif file_ext == '.opus':
            audio = OggOpus(str(file_path))
        elif file_ext == '.aiff':
            audio = AIFF(str(file_path))
        else:
            audio = MutagenFile(str(file_path))
        
        if audio is None:
            return False
            
        # Очищаем жанр перед обновлением
        if new_genre:
            # Сначала обрезаем по '/'
            clean_genre = new_genre.split('/')[0].strip()
            # Убираем символы '_' из начала названия папки
            clean_genre = clean_genre.lstrip('_')
        else:
            clean_genre = new_genre
            
        # Обновляем жанр - для MP3 используем TCON тег
        if file_ext == '.mp3':
            # Для MP3 используем TCON (Text Content) - стандартный тег для жанра в ID3v2
            # Создаем правильный объект TCON
            audio['TCON'] = TCON(encoding=3, text=clean_genre)
        else:
            # Для других форматов используем GENRE
            audio['GENRE'] = clean_genre
            
        audio.save()
        return True
        
    except Exception as e:
        print(f"      ❌ Ошибка обновления жанра: {str(e)}")
        return False

def move_file_to_genre_folder(file_path, genre_folder, genre, new_genre_name=None):
    """
    Перемещает файл в папку жанра и обновляет тег жанра
    """
    try:
        destination = genre_folder / file_path.name
        
        # Проверяем, не существует ли уже файл с таким именем
        if destination.exists():
            # Добавляем номер к имени файла
            counter = 1
            name_parts = file_path.stem, file_path.suffix
            while destination.exists():
                new_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
                destination = genre_folder / new_name
                counter += 1
        
        # Перемещаем файл
        shutil.move(str(file_path), str(destination))
        
        # Обновляем тег жанра в файле
        if new_genre_name and new_genre_name != genre:
            print(f"   🔄 Обновляю жанр в файле: '{genre}' → '{new_genre_name}'")
            if update_genre_in_file(destination, new_genre_name):
                print(f"   ✅ Жанр обновлен в файле")
            else:
                print(f"   ⚠️  Не удалось обновить жанр в файле")
        
        return destination
        
    except Exception as e:
        print(f"      ❌ Ошибка перемещения файла: {str(e)}")
        return None

def process_files_by_genre(search_directory=".", output_directory="."):
    """
    Обрабатывает файлы и перемещает их в папки по жанрам
    """
    search_path = Path(search_directory)
    output_path = Path(output_directory)
    
    if not search_path.exists():
        print(f"❌ Директория поиска {search_directory} не существует!")
        return
    
    if not output_path.exists():
        print(f"❌ Директория вывода {output_directory} не существует!")
        return
    
    print(f"🎵 Ищу файлы в: {search_path.absolute()}")
    print(f"📁 Создаю папки жанров в: {output_path.absolute()}")
    print(f"🔍 Ищу аудиофайлы...")
    
    # Поддерживаемые форматы
    audio_extensions = ['.flac', '.FLAC', '.mp3', '.MP3', '.m4a', '.M4A', 
                       '.mp4', '.MP4', '.ogg', '.OGG', '.opus', '.OPUS',
                       '.aiff', '.AIFF']
    
    # Счетчики для статистики
    total_files = 0
    moved_files = 0
    no_genre_files = 0
    errors = 0
    genres_found = set()
    created_folders = set()
    existing_folders = set()
    
    # Ищем все аудиофайлы только в корне директории поиска (без подпапок)
    audio_files = []
    for ext in audio_extensions:
        found_files = list(search_path.glob(f"*{ext}"))
        audio_files.extend(found_files)
    
    if not audio_files:
        print(f"❌ Аудиофайлы не найдены!")
        print(f"🔍 Поддерживаемые форматы: {', '.join(audio_extensions)}")
        return
    
    print(f"🎧 Найдено {len(audio_files)} аудиофайлов")
    
    # Создаем папку "Unknown" для файлов без жанра в директории вывода
    unknown_folder = output_path / "Unknown"
    
    # Обрабатываем каждый файл
    for i, audio_file in enumerate(audio_files, 1):
        # Проверяем, не было ли прерывания
        if interrupted:
            print("\n⏹️  Обработка прервана пользователем")
            break
            
        print(f"\n🎵 [{i}/{len(audio_files)}] Обрабатываю: {audio_file.name}")
        print(f"   📂 Текущий путь: {audio_file.parent}")
        
        try:
            total_files += 1
            
            # Получаем жанр из файла
            genre = get_genre_from_file(audio_file)
            
            if not genre:
                print(f"   ⚠️  Жанр не найден, перемещаю в папку 'Unknown'")
                genre = "Unknown"
                no_genre_files += 1
            else:
                print(f"   🎭 Жанр: {genre}")
                genres_found.add(genre)
            
            # Создаем папку для жанра (с интерактивным выбором)
            genre_folder, new_genre_name, is_custom, was_created = create_genre_folder(output_path, genre, audio_file)
            if not genre_folder:
                errors += 1
                continue
            
            # Обновляем статистику папок
            if was_created:
                created_folders.add(new_genre_name)
            else:
                existing_folders.add(new_genre_name)
            
            # Перемещаем файл (обновление тега жанра происходит внутри функции)
            destination = move_file_to_genre_folder(audio_file, genre_folder, genre, new_genre_name)
            if destination:
                moved_files += 1
                print(f"   ✅ Перемещен в: {destination}")
            else:
                errors += 1
                
        except Exception as e:
            errors += 1
            print(f"   ❌ ОШИБКА: {str(e)}")
    
    # Выводим статистику
    print(f"\n" + "="*60)
    print(f"📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
    print(f"   🎵 Всего файлов обработано: {total_files}")
    print(f"   ✅ Успешно перемещено: {moved_files}")
    print(f"   ⚠️  Без жанра (в папку 'Unknown'): {no_genre_files}")
    print(f"   ❌ Ошибок: {errors}")
    print(f"   🎭 Найдено жанров: {len(genres_found)}")
    
    if genres_found:
        print(f"\n🎭 Найденные жанры:")
        for genre in sorted(genres_found):
            print(f"   - {genre}")
    
    if created_folders:
        print(f"\n📁 Созданные папки:")
        for folder in sorted(created_folders):
            print(f"   - {folder}")
    
    if existing_folders:
        print(f"\n📂 Существующие папки:")
        for folder in sorted(existing_folders):
            print(f"   - {folder}")
    
    if no_genre_files > 0:
        print(f"\n📁 Файлы без жанра перемещены в папку: Unknown")
    
    print(f"="*60)

def get_search_directory():
    """
    Получает директорию для поиска файлов
    """
    print(f"\n🔍 Где искать аудиофайлы?")
    print(f"📁 1. В текущей директории")
    print(f"   {Path('.').absolute()}")
    print(f"📂 2. Указать другую директорию")
    print(f"🚪 q. Выход")
    
    while True:
        try:
            choice = safe_input(f"\n🎯 ➤ Выберите опцию (1-2, q для выхода): ")
            
            if choice == "1":
                search_dir = "."
                print(f"\n✅ 🎯 Выбрано: текущая директория")
                print(f"   📍 Путь: {Path('.').absolute()}")
                break
            elif choice == "2":
                search_path = safe_input(f"\n📁 ✏️  Введите путь для поиска файлов (q для выхода): ")
                if not search_path:
                    print("❌ ⚠️  Путь не может быть пустым!")
                    continue
                search_dir = search_path
                if not Path(search_dir).exists():
                    print(f"❌ ⚠️  Директория {search_dir} не существует!")
                    continue
                print(f"\n✅ 🎯 Выбрано: кастомная директория")
                print(f"   📍 Путь: {Path(search_dir).absolute()}")
                break
            else:
                print("❌ ⚠️  Неверный выбор! Введите число от 1 до 2")
                
        except ValueError:
            print("❌ ⚠️  Введите корректное число!")
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            return None, None
    
    return search_dir, None

def get_output_directory():
    """
    Получает директорию для создания подпапок жанров
    """
    print(f"\n📁 Где создавать папки жанров?")
    print(f"📁 1. В текущей директории")
    print(f"   {Path('.').absolute()}")
    print(f"📂 2. Указать другую директорию")
    print(f"🚪 q. Выход")
    
    while True:
        try:
            choice = safe_input(f"\n🎯 ➤ Выберите опцию (1-2, q для выхода): ")
            
            if choice == "1":
                output_dir = "."
                print(f"\n✅ 🎯 Выбрано: текущая директория")
                print(f"   📍 Папки жанров будут созданы в: {Path('.').absolute()}")
                break
            elif choice == "2":
                output_path = safe_input(f"\n📁 ✏️  Введите путь для создания папок жанров (q для выхода): ")
                if not output_path:
                    print("❌ ⚠️  Путь не может быть пустым!")
                    continue
                output_dir = output_path
                # Создаем директорию если её нет
                try:
                    Path(output_dir).mkdir(parents=True, exist_ok=True)
                    print(f"\n✅ 🎯 Выбрано: кастомная директория")
                    print(f"   📍 Папки жанров будут созданы в: {Path(output_dir).absolute()}")
                except Exception as e:
                    print(f"❌ ⚠️  Ошибка создания директории: {e}")
                    continue
                break
            else:
                print("❌ ⚠️  Неверный выбор! Введите число от 1 до 2")
                
        except ValueError:
            print("❌ ⚠️  Введите корректное число!")
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            return None
    
    return output_dir

def main():
    """
    Главная функция
    """
    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🎵 Скрипт перемещения файлов по жанрам")
    print("=" * 50)
    print("⚠️  ВНИМАНИЕ: Этот скрипт перемещает файлы!")
    print("   Убедитесь, что у вас есть резервная копия!")
    print()
    print("💡 Подсказка: В любой момент можно выйти, введя 'q' или нажав Ctrl+C")
    print("=" * 50)
    
    # Получаем директорию для поиска файлов
    search_dir, _ = get_search_directory()
    if search_dir is None:
        return
    
    # Получаем директорию для создания папок жанров
    output_dir = get_output_directory()
    if output_dir is None:
        return
    
    # Показываем параметры операции
    print(f"\n🎵 Начинаем обработку файлов:")
    print(f"🔍 Ищем файлы в: {Path(search_dir).absolute()}")
    print(f"📁 Создаем папки жанров в: {Path(output_dir).absolute()}")
    print(f"📋 Файлы будут перемещены в подпапки по жанрам!")
    
    try:
        process_files_by_genre(search_dir, output_dir)
    except KeyboardInterrupt:
        print("\n\n⏹️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")

if __name__ == "__main__":
    main()
