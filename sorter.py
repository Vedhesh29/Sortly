import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

move_history = []

def get_file_year(file_path):
    try:
        timestamp = os.path.getctime(file_path)
    except Exception:
        timestamp = os.path.getmtime(file_path)
    dt = datetime.fromtimestamp(timestamp)
    return str(dt.year)

def is_music(file_path):
    try:
        audio = MP3(file_path, ID3=EasyID3)
        title = audio.get("title", [None])[0]
        artist = audio.get("artist", [None])[0]
        genre = audio.get("genre", [None])[0]
        if title and artist:
            return True
        if genre and genre.lower() in ["pop", "rock", "hip hop", "electronic", "jazz", "classical"]:
            return True
    except Exception:
        pass
    return False

def record_move(src, dst, type_):
    move_history.append({
        "source": str(src),
        "destination": str(dst),
        "type": type_
    })

def move_file(file_path, target_dir):
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file_path.name
    record_move(file_path, target_path, "file")
    shutil.move(str(file_path), target_path)
    print(f"Moved {file_path} -> {target_path}")

def scan_and_sort(folder_path, config, behavior):
    folder = Path(folder_path)
    move_history.clear()
    summary = {}

    # --- Handle pre-existing folders ---
    if behavior == "Move pre-existing folders to archive":
        archive_path = folder / "Archived_Folders"
        archive_path.mkdir(exist_ok=True)

        for item in folder.iterdir():
            if item.is_dir() and item != archive_path and item.name not in [rule["folder"] for rule in config.values()]:
                target = archive_path / item.name
                record_move(item, target, "folder")
                shutil.move(str(item), target)
                # Add to summary using relative path
                rel_path = target.relative_to(folder)
                summary[str(rel_path)] = summary.get(str(rel_path), 0) + len(list(target.rglob("*")))

    # --- Gather files to sort ---
    if behavior == "Sort contents of pre-existing folders":
        files = [f for f in folder.rglob("*") if f.is_file()]
    else:
        files = [f for f in folder.glob("*") if f.is_file()]

    # --- Sort files according to rules ---
    for file in files:
        ext = file.suffix.lower()
        rule = config.get(ext)
        if rule:
            target_folder = folder / rule["folder"]
            subfolder_type = rule.get("subfolder")
            if subfolder_type == "year":
                target_folder = target_folder / get_file_year(file)
            elif subfolder_type == "musictype":
                target_folder = target_folder / ("Music" if is_music(file) else "Other")
            move_file(file, target_folder)
            # Update summary using relative path
            rel_path = target_folder.relative_to(folder)
            summary[str(rel_path)] = summary.get(str(rel_path), 0) + 1

    # --- Save move history ---
    Path("logs").mkdir(exist_ok=True)
    with open("logs/move_history.json", "w") as f:
        json.dump(move_history, f, indent=2)

    print("\nSorting complete.")
    return summary

