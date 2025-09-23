import argparse
import os
import random
from collections import defaultdict, Counter

def parse_args():
    parser = argparse.ArgumentParser(description="Split a .mgf file into balanced subsets by PTM modifications.")
    parser.add_argument('--input', required=True, help='Path to input .mgf file')
    parser.add_argument('--output_dir', required=True, help='Directory to save split files')
    parser.add_argument('--modifications', nargs='+', default=['phospho', 'oxidation'], help='Modifications to include')
    return parser.parse_args()

def label_spectrum(title):
    t = title.lower()
    if 'phospho' in t:
        return 'phospho'
    elif 'oxidation' in t:
        return 'oxidation'
    elif 'k_gg' in t or 'ubiquitin' in t:
        return 'k_gg'
    elif 'k_ac' in t or 'acetyl' in t:
        return 'k_ac'
    else:
        return 'unmodified'

def read_mgf(path):
    spectra = []
    with open(path) as f:
        current = []
        for line in f:
            line = line.strip()
            if line == 'BEGIN IONS':
                current = [line]
            elif line == 'END IONS':
                current.append(line)
                spectra.append('\n'.join(current))
            else:
                current.append(line)
    return spectra

def ask_user_for_split(total_spectra):
    recommended = 1200
    suggested_files = total_spectra // recommended + (1 if total_spectra % recommended != 0 else 0)
    print(f"\n📊 Found {total_spectra} spectra in file.")
    print(f"✅ Recommended: {recommended} spectra per file → {suggested_files} files.")

    user_input = input("Do you want to use this split? [Y/n]: ").strip().lower()
    if user_input in ('', 'y', 'yes'):
        return recommended
    else:
        while True:
            try:
                custom = int(input("Enter your custom number of spectra per file: "))
                if custom <= 0:
                    raise ValueError
                return custom
            except ValueError:
                print("Please enter a valid positive integer.")

def check_balance(labels, mods):
    counts = Counter(labels)
    min_count = min(counts[mod] for mod in mods if mod in counts)
    max_count = max(counts[mod] for mod in mods if mod in counts)
    print("\n🔎 Class distribution:")
    for mod in mods:
        print(f" - {mod}: {counts[mod]}")
    print(f" - unmodified: {counts['unmodified']}")
    if max_count - min_count > 0.1 * max_count:
        print("\n⚠️ Warning: The dataset is imbalanced. Balanced splitting may not be possible across all files.")

def split_spectra_balanced(spectra, labels, mods, per_file):
    from math import ceil
    buckets = defaultdict(list)

    for s, label in zip(spectra, labels):
        if label in mods or label == 'unmodified':
            buckets[label].append(s)

    # Compute class proportions
    total_spectra = sum(len(bucket) for bucket in buckets.values())
    proportions = {label: len(bucket) / total_spectra for label, bucket in buckets.items()}

    # Shuffle each class bucket
    for bucket in buckets.values():
        random.shuffle(bucket)

    result = []
    while sum(len(bucket) for bucket in buckets.values()) >= 1:
        current_batch = []
        for label, prop in proportions.items():
            bucket = buckets[label]
            n = ceil(per_file * prop)
            to_add = bucket[:n]
            current_batch.extend(to_add)
            buckets[label] = bucket[n:]

        if current_batch:
            random.shuffle(current_batch)  # Shuffle inside each file
            result.append(current_batch)

    return result


def write_splits(splits, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for i, spectra in enumerate(splits):
        with open(os.path.join(out_dir, f"split_file_{i+1:03d}.mgf"), 'w') as f:
            f.write('\n'.join(spectra))

def main():
    args = parse_args()
    spectra_blocks = read_mgf(args.input)

    titles = [line.split("TITLE=", 1)[1] for block in spectra_blocks for line in block.splitlines() if line.startswith("TITLE=")]
    labels = [label_spectrum(t) for t in titles]

    total = len(spectra_blocks)
    check_balance(labels, args.modifications)
    per_file = ask_user_for_split(total)

    splits = split_spectra_balanced(spectra_blocks, labels, args.modifications, per_file)
    write_splits(splits, args.output_dir)

    print(f"\n🎉 Done. Saved {len(splits)} split files to '{args.output_dir}'")

if __name__ == '__main__':
    main()
