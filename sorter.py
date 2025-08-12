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

def move_file(file_path, base_folder, subfolder=None, summary=None):
    file_name = Path(file_path).name
    target_dir = Path(base_folder)

    if subfolder == "year":
        year = get_file_year(file_path)
        target_dir = target_dir / year
    elif subfolder == "musictype":
        target_dir = target_dir / ("Music" if is_music(file_path) else "Other")

    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file_name

    move_history.append({"source": str(file_path), "destination": str(target_path)})
    shutil.move(str(file_path), target_path)
    print(f"Moved {file_path} -> {target_path}")

    # Track in summary
    if summary is not None:
        key = str(target_dir.relative_to(file_path.parent.parent if subfolder else file_path.parent))
        summary[key] = summary.get(key, 0) + 1

def scan_and_sort(folder_path, config, behavior):
    folder = Path(folder_path)
    move_history.clear()
    summary = {}

    # Step 1: Handle folder behavior
    if behavior == "Sort contents of pre-existing folders":
        files = list(folder.rglob("*"))  # All files including subfolders
    elif behavior == "Move pre-existing folders to archive":
        archive_path = folder / "Archived_Folders"
        archive_path.mkdir(exist_ok=True)
        for item in folder.iterdir():
            if item.is_dir() and item.name not in [rule["folder"] for rule in config.values()]:
                shutil.move(str(item), archive_path / item.name)
        files = list(folder.glob("*"))  # Only top-level files after moving folders
    else:  # "Leave pre-existing folders alone"
        files = list(folder.glob("*"))

    # Step 2: Sort files based on rules
    for file in files:
        if file.is_file():
            ext = file.suffix.lower()
            rule = config.get(ext)
            if rule:
                target_folder = folder / rule["folder"]
                subfolder = rule.get("subfolder")
                move_file(file, target_folder, subfolder, summary)

    # Save move history for undo
    Path("logs").mkdir(exist_ok=True)
    with open("logs/move_history.json", "w") as f:
        json.dump(move_history, f, indent=2)

    return summary  
