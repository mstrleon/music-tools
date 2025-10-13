import sys
import os
import re
from mutagen.flac import FLAC

def strip_color_prefix(comment):
    # Заменяем все вхождения 'color=' на '', не трогая значение
    return re.sub(r'\bcolor=', '', comment)

def process_file(filepath):
    try:
        audio = FLAC(filepath)
        changed = False

        if "comment" in audio:
            old_comments = audio["comment"]
            new_comments = [strip_color_prefix(c) for c in old_comments]
            if old_comments != new_comments:
                audio["comment"] = new_comments
                changed = True

        if changed:
            audio.save()
            print(f"✅ Updated: {filepath}")
        else:
            print(f"👌 No changes needed: {filepath}")
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")

def process_directory(directory):
    """Recursively process all FLAC files in a directory"""
    flac_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.flac'):
                filepath = os.path.join(root, file)
                process_file(filepath)
                flac_count += 1
    
    if flac_count == 0:
        print(f"📁 No FLAC files found in: {directory}")
    else:
        print(f"📁 Processed {flac_count} FLAC files in: {directory}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python strip_color_prefix.py file1.flac [file2.flac ...] [directory1] [directory2] ...")
        print("  - Files: Process individual FLAC files")
        print("  - Directories: Recursively process all FLAC files in the directory")
    else:
        for path in sys.argv[1:]:
            if os.path.isfile(path):
                if path.lower().endswith(".flac"):
                    process_file(path)
                else:
                    print(f"⚠️ Skipping non-FLAC file: {path}")
            elif os.path.isdir(path):
                process_directory(path)
            else:
                print(f"⚠️ Path not found: {path}")