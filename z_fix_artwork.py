import sys
import os
from mutagen.flac import FLAC, Picture

def extract_and_reembed_artwork(flac_path):
    audio = FLAC(flac_path)

    # Найдём первое изображение (если оно уже есть)
    if not audio.pictures:
        print(f"❌ No artwork found in {flac_path}")
        return

    picture = audio.pictures[0]  # Берём первое изображение

    # Удалим все текущие обложки — на всякий случай
    audio.clear_pictures()

    # Повторно добавим корректно
    new_pic = Picture()
    new_pic.data = picture.data
    new_pic.type = 3  # Front Cover
    new_pic.mime = picture.mime
    new_pic.desc = "Cover"
    new_pic.width = picture.width
    new_pic.height = picture.height
    new_pic.depth = picture.depth
    new_pic.colors = picture.colors

    audio.add_picture(new_pic)
    audio.save()
    print(f"✅ Fixed artwork in: {flac_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_flac_artwork.py path/to/file.flac")
    else:
        for path in sys.argv[1:]:
            if os.path.isfile(path) and path.lower().endswith(".flac"):
                extract_and_reembed_artwork(path)
            else:
                print(f"⚠️ Skipping: {path}")