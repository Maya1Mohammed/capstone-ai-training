import os
import yaml

# ── CONFIGURE THESE ──────────────────────────────────────────────
DATASET_ROOT = "./Media"  # folder containing train/, valid/, test/
CLASSES_TO_REMOVE = ['Bodypanel-Dent', 'RunningBoard-Dent', 'Signlight-Damage', 'pillar-dent', 'roof-dent']              # add any others here
# ─────────────────────────────────────────────────────────────────

yaml_path = os.path.join(DATASET_ROOT, "data.yaml")

# Load yaml
with open(yaml_path, "r") as f:
    data = yaml.safe_load(f)

all_classes = data['names']
remove_indices = {i for i, name in enumerate(all_classes) if name in CLASSES_TO_REMOVE}
kept_classes = [name for name in all_classes if name not in CLASSES_TO_REMOVE]

# Build remapping: old index -> new index
remap = {}
new_idx = 0
for old_idx, name in enumerate(all_classes):
    if old_idx not in remove_indices:
        remap[old_idx] = new_idx
        new_idx += 1

print(f"Removing classes: {CLASSES_TO_REMOVE}")
print(f"Removed indices: {remove_indices}")
print(f"Remaining classes ({len(kept_classes)}): {kept_classes}")

# Process label files in all splits
splits = ['train', 'valid', 'test']
removed_annotations = 0
emptied_files = 0

for split in splits:
    label_dir = os.path.join(DATASET_ROOT, split, "labels")
    if not os.path.exists(label_dir):
        continue
    for filename in os.listdir(label_dir):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(label_dir, filename)
        with open(filepath, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            class_idx = int(parts[0])
            if class_idx in remove_indices:
                removed_annotations += 1
                continue
            # Remap the index
            parts[0] = str(remap[class_idx])
            new_lines.append(" ".join(parts) + "\n")
        
        if not new_lines:
            emptied_files += 1
        
        with open(filepath, "w") as f:
            f.writelines(new_lines)

# Update data.yaml
data['names'] = kept_classes
data['nc'] = len(kept_classes)
with open(yaml_path, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"\nDone!")
print(f"  Annotations removed: {removed_annotations}")
print(f"  Label files now empty: {emptied_files}")
print(f"  data.yaml updated: nc={len(kept_classes)}")