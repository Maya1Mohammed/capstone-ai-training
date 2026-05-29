import os
from PIL import Image

BASE_DIR = "VW ID4"

removed = 0
checked = 0

for root, dirs, files in os.walk(BASE_DIR):
    if "rejected" in root:
        continue
    for fname in files:
        if not fname.endswith(".jpg"):
            continue
        fpath = os.path.join(root, fname)
        checked += 1
        try:
            img = Image.open(fpath)
            img.verify()
        except Exception:
            print(f"Corrupt, removing: {fpath}")
            os.remove(fpath)
            removed += 1

print(f"\nChecked {checked} images. Removed {removed} corrupt files.")