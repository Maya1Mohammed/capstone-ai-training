# Training (Image Scraping + Model Training)

This folder contains the end-to-end workflow used in the capstone project:

1. **Web-scrape images** for the classification dataset (used by the ResNet training).
2. **Clean + balance** the scraped dataset.
3. **Train multiple AI models** using the prepared datasets.

> Note: the `scraper/` folder was specifically used to web-scrape images to build inputs for `resnet_training/`. The other folders are separate training pipelines for different models.

---

## Repository Structure

- `scraper/`
  - Scripts to fetch car images from the web, validate them, and prepare a structured dataset.
  - Also includes dataset balancing/augmentation utilities and progress tracking.
- `resnet_training/`
  - PyTorch ResNet50-based **multi-head classifier** training.
  - Predicts **make**, **model**, and **year_range** from images.
- `random_forest_training/`
  - Scikit-learn RandomForest regressor training.
  - Predicts **price** using encoded categorical features.
- `yolo_training/`
  - YOLO training pipeline (YOLOv8 style dataset/export).
  - Dataset documentation included (Roboflow export).

---

## scraper/ (Web scraping + dataset preparation)

### Key scripts
- `scrape_fusion_images.py`
  - Scrapes **Ford Fusion** images by year and view (front/rear/side/full_body).
  - Uses DuckDuckGo image results.
  - Performs basic image validation (size/aspect/colors/content-type) and rejects poor images.
  - Writes output into a local folder structure and tracks progress in `progress.json`.

- `scrape_id4_images.py`
  - Same approach for **Volkswagen ID.4**.
  - Uses `progress_id4.json` for resumable scraping.

- `scrape_estar_images.py`
  - Same approach for **Changan Estar**.
  - Uses `progress_estar.json` for resumable scraping.

- `verify_images.py`
  - Walks through the downloaded dataset and removes corrupt/unreadable `.jpg` files.

- `augment_dataset.py`
  - Runs once to create a **balanced** dataset size per class/angle folder.
  - Uses Albumentations-based augmentations (flip/rotate/color/blur/crop, etc.).
  - Command-line usage (from the script docstring):
    - `python augment_dataset.py --src ./dataset_root --dst ./dataset_balanced --target 350`

### What it produces
A structured dataset under each car root (e.g., the scripts use folders such as `Ford Fusion`, `VW ID4`, `Changan Estar`) with subfolders by:
- `year range` (group)
- `view` (front/rear/side/full_body)
- plus a `rejected/` folder for rejected downloads

Those saved/validated images are what you train on in `resnet_training/`.

---

## resnet_training/ (Multi-head ResNet50 classifier)

- `CarDetection.ipynb`
  - Uses a pretrained **ResNet50** backbone.
  - Replaces the final layer with three classification heads:
    - `make`
    - `model`
    - `year_range`
  - Creates and saves label encoders (JSON mappings) so predictions can be decoded later.
  - Trains with augmentation (random flips/rotations/color jitter, normalization).
  - Saves the best checkpoint to `checkpoints/best_model.pth` (in the configured Google Drive path).

---

## random_forest_training/ (Price regression)

- `SparePartPredictor.ipynb`
  - Trains `RandomForestRegressor` to predict `price`.
  - Uses `LabelEncoder` for categorical inputs:
    - `make`
    - `model`
    - `year_range`
    - `part_name`
    - `part_condition`
  - Saves:
    - the trained model (`price_model.pkl`)
    - the feature encoders as JSON files.

---

## yolo_training/ (YOLO damage/scratch detection)

- `CarDent.ipynb`
  - YOLO model training using the dataset in `yolo_training/Media`.

- Dataset documentation
  - `README.dataset.txt` / `README.roboflow.txt`
  - Dataset provenance: Roboflow export
  - Includes the number of images and that annotations are in **YOLOv8 format**.

---

## Notes

- The notebooks under each training folder are designed for interactive environments (e.g., Google Colab).
- Dataset locations in the training notebooks may reference Google Drive paths; update those paths if you run locally.

