import argparse
from sorter import scan_and_sort

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart File Sorter")
    parser.add_argument("folder", help="Folder to sort")
    args = parser.parse_args()
    
    scan_and_sort(args.folder)
