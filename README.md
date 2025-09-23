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
  * contains `k_gg` or `ubiquitin` → `k_gg`
  * contains `k_ac` or `acetyl` → `k_ac`
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

