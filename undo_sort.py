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

    # Sort by path depth descending to safely undo nested files/folders
    moves_sorted = sorted(moves, key=lambda x: len(Path(x["destination"]).parts), reverse=True)

    for move in reversed(moves_sorted):
        src = Path(move["destination"])
        dst = Path(move["source"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src.exists():
                shutil.move(str(src), str(dst))
                print(f"Restored {move['type'].capitalize()} {src} -> {dst}")
        except Exception as e:
            print(f"Error restoring {src}: {e}")

    # Clean up empty folders created during sort
    all_folders = {Path(m['destination']).parent for m in moves_sorted}
    for folder in sorted(all_folders, key=lambda x: len(x.parts), reverse=True):
        try:
            while folder.exists() and folder != folder.parent and not any(folder.iterdir()):
                folder.rmdir()
                print(f"Deleted empty folder: {folder}")
                folder = folder.parent
        except Exception as e:
            print(f"Error cleaning folder {folder}: {e}")

    history_path.unlink()
    print("\nUndo complete.")

if __name__ == "__main__":
    undo_moves()
