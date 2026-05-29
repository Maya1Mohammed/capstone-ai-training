import os
import requests
import time
import hashlib
import json
from duckduckgo_search import DDGS
from PIL import Image
from io import BytesIO

# ── Settings ──────────────────────────────────────────────────────────────────
BASE_DIR        = "Changan Estar"
TARGET_PER_VIEW = 94
OVERSCRAPE_MULT = 2.0
SCRAPE_PER_VIEW = int(TARGET_PER_VIEW * OVERSCRAPE_MULT)  # 188
MIN_WIDTH       = 400
MIN_HEIGHT      = 300
MIN_COLORS      = 300
PROGRESS_FILE   = "progress_estar.json"  # separate from other progress files
# ──────────────────────────────────────────────────────────────────────────────

GROUPS = {
    "2020-2026": range(2020, 2027),
}

VIEWS = {
    "front": [
        "Changan Estar {year} front view photo",
        "Changan Estar {year} front exterior photograph",
        "Changan Estar {year} headlights front",
        "{year} Changan Estar front bumper photo",
        "Changan Estar {year} front angle shot",
        "{year} Changan Estar nose front grille photo",
    ],
    "rear": [
        "Changan Estar {year} rear view photo",
        "Changan Estar {year} back exterior photograph",
        "Changan Estar {year} taillights rear",
        "{year} Changan Estar rear bumper photo",
        "Changan Estar {year} rear angle shot",
        "{year} Changan Estar trunk rear photo",
    ],
    "side": [
        "Changan Estar {year} side view photo",
        "Changan Estar {year} side profile photograph",
        "Changan Estar {year} side exterior",
        "{year} Changan Estar side shot",
        "Changan Estar {year} door side panel photo",
        "{year} Changan Estar lateral side view",
    ],
    "full_body": [
        "Changan Estar {year} full body photo",
        "Changan Estar {year} full exterior photograph",
        "Changan Estar {year} whole car photo",
        "{year} Changan Estar complete car shot",
        "Changan Estar {year} 3/4 view photo",
        "{year} Changan Estar listing photo exterior",
    ],
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ── Progress tracker ──────────────────────────────────────────────────────────
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
            data["completed"] = set(data["completed"])
            data["seen_urls"] = set(data["seen_urls"])
            return data
    return {"completed": set(), "seen_urls": set()}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({
            "completed": list(progress["completed"]),
            "seen_urls": list(progress["seen_urls"]),
        }, f, indent=2)

def progress_key(year, group_name, view):
    return f"{year}_{group_name}_{view}"

# ── Folder setup ──────────────────────────────────────────────────────────────
def make_folders():
    for group in GROUPS:
        for view in VIEWS:
            os.makedirs(os.path.join(BASE_DIR, group, view), exist_ok=True)
        os.makedirs(os.path.join(BASE_DIR, group, "rejected"), exist_ok=True)

# ── Image cleaning ────────────────────────────────────────────────────────────
def clean_image(img_bytes):
    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        w, h = img.size
        if w < MIN_WIDTH or h < MIN_HEIGHT:
            return False, f"too_small_{w}x{h}"
        aspect = w / h
        if aspect < 0.8 or aspect > 3.5:
            return False, f"bad_aspect_{aspect:.2f}"
        img_small = img.resize((50, 50))
        pixels = list(img_small.getdata())
        unique_colors = len(set(pixels))
        if unique_colors < MIN_COLORS:
            return False, f"low_colors_{unique_colors}"
        return True, "ok"
    except Exception as e:
        return False, f"error_{str(e)[:30]}"

# ── Download ──────────────────────────────────────────────────────────────────
def download_image(url, good_path, rejected_path, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10, stream=True)
            if resp.status_code != 200:
                return "failed"
            content_type = resp.headers.get("Content-Type", "")
            if not content_type.startswith("image"):
                return "failed"
            if "gif" in content_type or "svg" in content_type:
                return "failed"
            img_bytes = resp.content
            is_good, reason = clean_image(img_bytes)
            if is_good:
                with open(good_path, "wb") as f:
                    f.write(img_bytes)
                return "saved"
            else:
                with open(rejected_path, "wb") as f:
                    f.write(img_bytes)
                return f"rejected:{reason}"
        except Exception:
            if attempt < retries - 1:
                time.sleep(2)
    return "failed"

# ── Scrape one view for one year ──────────────────────────────────────────────
def scrape_view(year, group_name, view, good_folder, rejected_folder, progress):
    queries = [q.format(year=year) for q in VIEWS[view]]
    key     = progress_key(year, group_name, view)

    existing = [
        f for f in os.listdir(good_folder)
        if f.startswith(f"{year}_{view}_")
    ]
    saved    = len(existing)
    rejected = 0

    if saved >= SCRAPE_PER_VIEW:
        print(f"    Already complete ({saved} images). Skipping.")
        progress["completed"].add(key)
        save_progress(progress)
        return saved, 0

    if saved > 0:
        print(f"    Resuming from {saved}/{SCRAPE_PER_VIEW} images...")

    for query in queries:
        if saved >= SCRAPE_PER_VIEW:
            break

        print(f"    [{saved}/{SCRAPE_PER_VIEW}] Searching: \"{query}\"")

        results = []
        for attempt in range(3):
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.images(
                        query,
                        max_results=100,
                        type_image="photo",
                        size="large",
                    ))
                break
            except Exception as e:
                print(f"    Search error (attempt {attempt+1}): {e}")
                time.sleep(4)

        for r in results:
            if saved >= SCRAPE_PER_VIEW:
                break

            url = r.get("image", "")
            if not url:
                continue

            if url in progress["seen_urls"]:
                continue

            progress["seen_urls"].add(url)
            save_progress(progress)

            if any(url.lower().endswith(x) for x in [".svg", ".gif"]):
                continue

            good_path     = os.path.join(good_folder,     f"{year}_{view}_{saved+1:04d}.jpg")
            rejected_path = os.path.join(rejected_folder, f"{year}_{view}_rej_{rejected+1:04d}.jpg")

            result = download_image(url, good_path, rejected_path)

            if result == "saved":
                saved += 1
                if saved % 20 == 0:
                    print(f"    ✓ {saved}/{SCRAPE_PER_VIEW} saved ({rejected} rejected so far)")
            elif result.startswith("rejected"):
                rejected += 1

            time.sleep(0.4)

        time.sleep(2)

    progress["completed"].add(key)
    save_progress(progress)
    return saved, rejected

# ── Main ──────────────────────────────────────────────────────────────────────
make_folders()
progress = load_progress()

if progress["completed"]:
    print(f"Resuming — {len(progress['completed'])} view/year combos already done.")
    print(f"Seen URLs so far: {len(progress['seen_urls'])}\n")
else:
    print("Starting fresh.\n")

grand_total_saved    = 0
grand_total_rejected = 0

for group_name, years in GROUPS.items():
    print(f"\n{'='*60}")
    print(f"GROUP: {group_name}")
    print(f"{'='*60}")

    good_base     = os.path.join(BASE_DIR, group_name)
    rejected_base = os.path.join(BASE_DIR, group_name, "rejected")

    for year in years:
        print(f"\n  Year: {year}")

        for view in VIEWS:
            key = progress_key(year, group_name, view)

            if key in progress["completed"]:
                print(f"\n  View: {view}  ← already complete, skipping")
                continue

            good_folder = os.path.join(good_base, view)
            print(f"\n  View: {view}  (target: {SCRAPE_PER_VIEW} scraped → {TARGET_PER_VIEW} clean)")

            saved, rejected = scrape_view(
                year, group_name, view, good_folder, rejected_base, progress
            )

            print(f"  ✓ {year} {view}: {saved} saved, {rejected} rejected")
            grand_total_saved    += saved
            grand_total_rejected += rejected
            time.sleep(2)

        time.sleep(3)

print(f"\n{'='*60}")
print(f"✅ All done!")
print(f"   Total saved:    {grand_total_saved}")
print(f"   Total rejected: {grand_total_rejected}")
print(f"   Saved to:       '{BASE_DIR}' folder")
print(f"{'='*60}")