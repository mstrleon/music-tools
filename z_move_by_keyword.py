import os
import shutil
import mutagen.flac
import mutagen.mp3
import mutagen

# Запрос данных
source_folder = input('📁 Введите путь к папке c FLAC/MP3/AIFF-файлами: ').strip()
destination_folder = input('📂 Введите путь для перемещения подходящих файлов: ').strip()
keyword = input('🔍 Введите ключевое слово для поиска в комментариях: ').strip().lower()

# Проверка и создание папки назначения
os.makedirs(destination_folder, exist_ok=True)

# Обработка файлов
for filename in os.listdir(source_folder):
    filepath = os.path.join(source_folder, filename)
    
    if filename.lower().endswith('.flac'):
        try:
            audio = mutagen.flac.FLAC(filepath)
            comments = audio.get('comment', [])

            if any(keyword in comment.lower() for comment in comments):
                print(f'✅ Найдено слово "{keyword}" в {filename} — перемещаем...')
                shutil.move(filepath, os.path.join(destination_folder, filename))

        except Exception as e:
            print(f'⚠️ Ошибка при обработке {filename}: {e}')
    
    elif filename.lower().endswith('.mp3'):
        try:
            audio = mutagen.File(filepath)
            comments = []
            
            # Получение комментариев из разных возможных тегов
            if audio is not None:
                # ID3v2 COMM фреймы
                if hasattr(audio, 'tags') and audio.tags:
                    for key in audio.tags:
                        if key.startswith('COMM'):
                            comments.extend([str(val) for val in audio.tags[key].text])
                    # Также проверяем простое поле comment
                    if 'comment' in audio.tags:
                        comments.extend(audio.tags['comment'])

            if any(keyword in comment.lower() for comment in comments):
                print(f'✅ Найдено слово "{keyword}" в {filename} — перемещаем...')
                shutil.move(filepath, os.path.join(destination_folder, filename))

        except Exception as e:
            print(f'⚠️ Ошибка при обработке {filename}: {e}')
    
    elif filename.lower().endswith(('.aiff', '.aif')):
        try:
            audio = mutagen.File(filepath)
            comments = []
            
            # Получение комментариев из AIFF тегов
            if audio is not None and hasattr(audio, 'tags') and audio.tags:
                # Проверяем ID3 теги (AIFF может содержать ID3)
                for key in audio.tags:
                    if key.startswith('COMM'):
                        comments.extend([str(val) for val in audio.tags[key].text])
                    if key == 'comment' or key == 'COMMENT':
                        val = audio.tags[key]
                        if isinstance(val, list):
                            comments.extend([str(v) for v in val])
                        else:
                            comments.append(str(val))

            if any(keyword in comment.lower() for comment in comments):
                print(f'✅ Найдено слово "{keyword}" в {filename} — перемещаем...')
                shutil.move(filepath, os.path.join(destination_folder, filename))

        except Exception as e:
            print(f'⚠️ Ошибка при обработке {filename}: {e}')

print('🎉 Завершено.')