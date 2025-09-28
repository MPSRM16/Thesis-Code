# Thesis-Code

# MGF Splitter (balanced by PTM labels)

A small command-line tool to split a large `.mgf` file into multiple smaller `.mgf` files while **preserving the class proportions** of spectra (by PTM label) in each split. Labels are inferred from the `TITLE` line (e.g., `phospho`, `oxidation`, `k_gg`, `k_ac`; anything else becomes `unmodified`). This is designed to create input chunks ready for your `DatasetHandler` class that consumes folders of `.mgf` files.&#x20;

## Features

* Reads one big `.mgf`, writes multiple `split_file_XXX.mgf` outputs.
* Tries to keep per-file class balance based on observed proportions.
* Interactive prompt recommends minium \~1200 spectra per file (you can and should increase this number if you have high level computational resources).&#x20;
* Simple, no external dependencies (pure Python).

## Requirements

* Python 3.8+ (no extra packages needed).

## Installation

```bash
# Option 1: run in place
python mgf_splitter.py --help

# Option 2: make it executable (Unix)
chmod +x mgf_splitter.py
./mgf_splitter.py --help
```

## Usage

```bash
python mgf_splitter.py \
  --input /path/to/big_dataset.mgf \
  --output_dir ./splits \
  --modifications phospho oxidation k_gg k_ac
```

### Arguments

* `--input` (required): path to the source `.mgf`.
* `--output_dir` (required): directory where split files will be written.
* `--modifications` (optional): list of labels to **treat as modified** and balance against (defaults to `phospho oxidation`). Any spectrum not matching these patterns is labeled `unmodified`. Label rules are:

  * contains `phospho` → `phospho`
  * contains `oxidation` → `oxidation`
  * contains `k_gg` a.k.a `ubiquitination` → `k_gg`
  * contains `k_ac` or `acetylation` → `k_ac`
  * otherwise → `unmodified`&#x20;

## Example

```bash
python mgf_splitter.py \
  --input ./data/all_spectra.mgf \
  --output_dir ./data/splits \
  --modifications phospho oxidation k_gg k_ac
```

**What happens:**

1. The tool scans the `.mgf`, extracts `TITLE` entries, and assigns labels using the rules above.
2. It prints the class distribution, warns if the dataset is imbalanced, and suggests a per-file size (\~1200).
3. It creates `split_file_001.mgf`, `split_file_002.mgf`, … in `./data/splits`, each trying to mirror the global class proportions.&#x20;

**Typical output:**

```
📊 Found 37,842 spectra in file.
✅ Recommended: 1200 spectra per file → 32 files.

🔎 Class distribution:
 - phospho: 8,120
 - oxidation: 10,004
 - k_gg: 1,230
 - k_ac: 520
 - unmodified: 17,968
⚠️ Warning: The dataset is imbalanced. Balanced splitting may not be possible across all files.

🎉 Done. Saved 32 split files to './data/splits'
```

## Notes & Limitations

* **Labeling depends on `TITLE` text.** If your upstream pipeline uses different strings, update `label_spectrum()` accordingly. Controlled vocabularies are not enforced, the labels used are based on the ones of the annotated spectra we used during the tranning and development of the model.&#x20;
* **Balance is approximate.** Extremely skewed datasets cannot be perfectly balanced per file; the script will warn you.&#x20;
* **Compatible with DatasetHandler** setups that expect a *directory of `.mgf` files* rather than one huge file.


# MS/MS Spectra Modification Classifier (Transformer-based)

This repository accompanies my master’s thesis and provides two Google-Colab-ready notebooks (exported as `.py`) for detecting and classifying post-translational modifications (PTMs) directly from shotgun proteomics MS/MS spectra. Both implement a hybrid CNN→Transformer architecture with precursor-mass fusion.  

## Contents

* `final_3_class_model.py` — three-category pipeline (Unmodified, Oxidation, Phosphorylation). It uses a one-vs-rest head design (sigmoid logits), while the current labeler maps each spectrum to a single class. This enables multi-label experiments without changing the backbone. 
* `final_5_class_model.py` — five-category pipeline (adds Ubiquitination and Acetylation) with a single softmax head (CrossEntropy). 

> Note: These files are exported from Colab; they retain the original narrative markdown and cell structure to facilitate academic reproducibility. This README is intentionally brief.

## Method (brief)

**Input & parsing.** Spectra are read from `.mgf` files; required fields include `TITLE`, `PEPMASS`, and `CHARGE`. A streaming `DatasetHandler` loads one file at a time to control memory footprint.  

**Preprocessing.** Peaks are binned over a fixed m/z range into dense 1D vectors, with *sliding-window normalization* to preserve local signal while damping region-dominant intensities.  

**Precursor handling.** Observed precursor m/z is converted to monoisotopic neutral mass (given charge) and min–max normalized to $0,1$; missing metadata defaults safely.  

**Architecture.** A 1D-CNN encoder extracts local patterns; features are projected, enhanced with sinusoidal positional encoding, and passed through a Transformer encoder. A small MLP encodes the normalized parent-ion feature; fusion occurs by concatenation before classification. In the 3-class file, classification uses independent heads; in the 5-class file, a single linear head outputs `num_classes` logits.  

**Labeling.** Heuristic labels are inferred from `TITLE`: “oxidation” → Oxidation; “phospho” → Phosphorylation; (5-class only) “k_gg” → Ubiquitination; “k_ac” → Acetylation; otherwise Unmodified.  

## Quick start (Colab)

1. **Open in Colab** and run the introductory cell to mount Drive:

   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
2. **Prepare Drive folders** (or adjust paths in the code):

   ```
   MyDrive/
   ├── data/
   │   └── balanced_dataset/      # .mgf files
   └── peak_encoder_transformer_pipeline/
       ├── model_weights/
       └── logs/
   ```

   The notebooks include `os.makedirs(...)` helpers and path variables you can edit near the top.  
3. **Run cells sequentially** (parsing → preprocessing → model → training/evaluation). Check the in-notebook logging for progress and metrics. Model weights and logs are persisted to the paths you configure. 

## Running locally (optional)

* Python ≥3.10 is recommended. Install core deps:

  ```bash
  pip install torch numpy scikit-learn matplotlib
  ```
* GPU acceleration is advised for training. You can execute the `.py` files as literate notebooks using Jupytext or open them in VS Code/PyCharm and run cell blocks.

## Training & evaluation

* **Imbalance handling.** The 3-class file uses independent sigmoid logits with BCE (weights supported); the 5-class file uses `CrossEntropyLoss` (optionally class-weighted). L1 regularization is available.  
* **Checkpointing & logs.** Checkpoints and `.log` files are written to your Drive under the configured directories. 

## Notes & limitations

* Label inference depends on consistent `TITLE` conventions; verify dataset naming to avoid silent mislabeling (especially for `k_gg` / `k_ac`). 

Got it — I’ll keep the spotlight on the splitter and models, and add only a short note at the end about the extra utilities. Append this to your README:

---

## Extras (brief)

**K-fold cross-validation.** Optional scripts to run (stratified) K-fold CV on your balanced `.mgf` splits, preserving PTM label proportions across folds. Works with both `final_3_class_model.py` and `final_5_class_model.py`, emitting per-fold metrics and an aggregated report.

**Optuna hyperparameter tuning.** Reproducible studies for key knobs (e.g., learning rate, weight decay, CNN channels, Transformer depth/heads, dropout, batch size). Includes pruning, best-trial checkpointing, and simple logging.

These utilities are optional and lightweight—they don’t change the core splitter or model pipelines. Check the repository’s scripts for quick usage examples.
