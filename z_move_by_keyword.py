import os
import shutil
import mutagen.flac

# Запрос данных
source_folder = input('📁 Введите путь к папке c FLAC-файлами: ').strip()
destination_folder = input('📂 Введите путь для перемещения подходящих файлов: ').strip()
keyword = input('🔍 Введите ключевое слово для поиска в комментариях: ').strip().lower()

# Проверка и создание папки назначения
os.makedirs(destination_folder, exist_ok=True)

# Обработка файлов
for filename in os.listdir(source_folder):
    if filename.lower().endswith('.flac'):
        filepath = os.path.join(source_folder, filename)

        try:
            audio = mutagen.flac.FLAC(filepath)
            comments = audio.get('comment', [])

            if any(keyword in comment.lower() for comment in comments):
                print(f'✅ Найдено слово "{keyword}" в {filename} — перемещаем...')
                shutil.move(filepath, os.path.join(destination_folder, filename))

        except Exception as e:
            print(f'⚠️ Ошибка при обработке {filename}: {e}')

print('🎉 Завершено.')