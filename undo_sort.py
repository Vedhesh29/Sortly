import json
import shutil
from pathlib import Path

def undo_moves():
    history_path = Path("logs/move_history.json")
    if not history_path.exists():
        print("No move history found.")
        return

    with open(history_path, "r") as f:
        moves = json.load(f)

    touched_folders = set()

    for move in reversed(moves):
        src = Path(move["destination"])
        dst = Path(move["source"])
        dst.parent.mkdir(parents=True, exist_ok=True)

        try:
            if src.exists():
                shutil.move(str(src), str(dst))
                print(f"Restored {src} -> {dst}")
                touched_folders.add(str(src.parent))
        except Exception as e:
            print(f"Error restoring {src}: {e}")

    # Clean up empty folders
    sorted_folders = sorted(touched_folders, key=lambda x: len(Path(x).parts), reverse=True)
    for folder in sorted_folders:
        try:
            folder_path = Path(folder)
            while folder_path != folder_path.parent:
                if any(folder_path.iterdir()):
                    break
                folder_path.rmdir()
                print(f"Deleted empty folder: {folder_path}")
                folder_path = folder_path.parent
        except Exception as e:
            print(f"Could not delete {folder}: {e}")

    history_path.unlink()
    print("\nUndo complete.")

if __name__ == "__main__":
    undo_moves()
