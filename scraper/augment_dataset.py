"""
augment_dataset.py — run once to produce a balanced dataset folder.

Usage:
  python augment_dataset.py --src ./dataset_root --dst ./dataset_balanced --target 350

Expected structure:
  dataset_root/
    ford_fusion/
      2010_2012/
        front/  rear/  side/  full_body/
      2013_2016/ ...
    vw_id4/
      2020_2026/
        front/  rear/  side/  full_body/
    changan_estar/
      2020_2026/
        front/  rear/  side/  full_body/
"""

import sys, random, shutil, argparse
from pathlib import Path
import cv2
import numpy as np
import albumentations as A
from tqdm import tqdm

PIPELINE = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.Rotate(limit=6, p=0.6),                          # small — car angle matters
    A.RandomBrightnessContrast(0.25, 0.20, p=0.7),
    A.HueSaturationValue(8, 20, 15, p=0.5),
    A.GaussNoise(var_limit=(5.0, 30.0), p=0.3),
    A.GaussianBlur(blur_limit=(3, 5), p=0.25),
    A.RandomResizedCrop(size=(224, 224), scale=(0.85, 1.0), p=0.4),
    A.CLAHE(clip_limit=2.0, p=0.2),
])

EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def get_images(folder):
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTS]

def augment(img):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return cv2.cvtColor(PIPELINE(image=rgb)["image"], cv2.COLOR_RGB2BGR)

def balance(src, dst, target, dry_run):
    dst.mkdir(parents=True, exist_ok=True)
    imgs = get_images(src)
    n = len(imgs)
    if n == 0:
        print(f"    [WARN] Empty: {src}"); return n, 0

    if n >= target:
        selected = random.sample(imgs, target)
        if not dry_run:
            for p in selected: shutil.copy2(p, dst / p.name)
        return n, target

    # copy originals
    if not dry_run:
        for p in imgs: shutil.copy2(p, dst / p.name)

    needed = target - n
    done = 0
    pbar = tqdm(total=needed, desc=f"    {src.name}", leave=False) if not dry_run else None

    while done < needed:
        p = random.choice(imgs)
        img = cv2.imread(str(p))
        if img is None: continue
        out = dst / f"{p.stem}_aug{done:04d}{p.suffix}"
        if not dry_run:
            cv2.imwrite(str(out), augment(img))
            pbar.update(1)
        done += 1

    if pbar: pbar.close()
    return n, n + done

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--target", type=int, default=350)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed); np.random.seed(args.seed)
    src, dst = Path(args.src), Path(args.dst)

    print(f"Source : {src}\nOutput : {dst}\nTarget : {args.target}/angle\n" + "-"*50)

    totals = []
    for car in sorted(src.iterdir()):
        if not car.is_dir(): continue
        print(f"\n[{car.name}]")
        for year in sorted(car.iterdir()):
            if not year.is_dir(): continue
            print(f"  [{year.name}]")
            for angle in sorted(year.iterdir()):
                if not angle.is_dir(): continue
                orig, final = balance(angle, dst/car.name/year.name/angle.name, args.target, args.dry_run)
                totals.append((orig, final))
                icon = "✓" if final == args.target else "~"
                print(f"    [{icon}] {angle.name:12s}  {orig:>4} → {final:>4}")

    o, f = sum(x[0] for x in totals), sum(x[1] for x in totals)
    print(f"\nOriginal: {o}  →  Balanced: {f}  ({f/max(o,1):.2f}x)")
    if not args.dry_run: print(f"Saved to: {dst}")

if __name__ == "__main__": main()