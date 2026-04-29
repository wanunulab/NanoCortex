# ReRNAFM User Guide

## Quick Start

ReRNAFM provides a unified command-line interface using a subcommand structure:

```bash
ReRNAFM <command> [arguments]
````

## View Help

```bash
# View all available commands
ReRNAFM --help

# View detailed help for a specific command
ReRNAFM embed --help
ReRNAFM predict_ss --help
ReRNAFM cluster --help
ReRNAFM classify --help
ReRNAFM predict_expression --help
```

## Command Details

### 1. embed - Generate RNA sequence embeddings

**Function**: Convert RNA sequences into numerical vectors (embeddings) for downstream analysis. Uses pretrained models, no training required.

**Basic Usage**:

```bash
# Provide sequences directly from command line
ReRNAFM embed --sequences "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU"

# Read sequences from file
ReRNAFM embed --sequences_file sequences.fasta --output embeddings.npy

# Full parameter example
ReRNAFM embed \
    --sequences_file sequences.fasta \
    --model_type rna \
    --device cuda \
    --repr_layer 12 \
    --mean_pool \
    --batch_size 32 \
    --output embeddings.npy
```

**Main Parameters**:

* `--sequences`: Provide sequences directly in command line (separate multiple sequences with spaces)
* `--sequences_file`: Read sequences from file (supports .fasta, .fa, .txt)
* `--model_type`: Model type (ss/rna/mrna), default rna
* `--device`: Compute device (cpu/cuda), auto-selected by default
* `--mean_pool`: Whether to apply mean pooling across sequence length
* `--output`: Save embeddings to file (.npy)

---

### 2. predict_ss - Predict RNA secondary structure

**Function**: Predict RNA secondary structure probability maps. Uses pretrained models, no training required.

**Basic Usage**:

```bash
# Smart output: specify directory, automatically generate all formats (named by sequence ID)
# Example: FASTA file contains >maqe, will generate maqe.png and maqe.ct
ReRNAFM predict_ss --sequences_file sequences.fasta --output ./results/

# Specify specific file format
ReRNAFM predict_ss --sequences_file sequences.fasta --output result.png  # save image only
ReRNAFM predict_ss --sequences_file sequences.fasta --output result.ct   # save structure file only
ReRNAFM predict_ss --sequences_file sequences.fasta --output result.npy  # save numeric result only

# Provide sequence from command line
ReRNAFM predict_ss --sequences "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU" --output ./results/
```

**Main Parameters**:

* `--sequences`: Sequence list
* `--sequences_file`: Sequence file path
* `--device`: Compute device
* `--output`: **Smart output path** (recommended)

  * Directory path (e.g., `./results/`): automatically generates all formats (.png and .ct) using sequence ID
  * File path: format inferred from extension (.npy, .png, .ct, etc.)
* `--threshold`: Base-pair probability threshold (default: 0.5)
* `--allow_nc`: Allow non-canonical pairs (default: disabled)

**Output Naming Rules**:

* Directory mode: use sequence ID (e.g., `>maqe` → `maqe.png`, `maqe.ct`)
* File mode: use specified filename

---

### 3. cluster - RNA family clustering visualization

**Function**: Perform clustering analysis on RNA sequences using t-SNE and visualize RNA family distributions. Uses pretrained embeddings, no training required.

**Basic Usage**:

```bash
# Basic usage
ReRNAFM cluster --fasta_folder /path/to/fasta/folder

# Full parameter example
ReRNAFM cluster \
    --fasta_folder /path/to/fasta/folder \
    --model_type rna \
    --device cuda \
    --batch_size 32 \
    --output clustering_result.png \
    --n_components 2 \
    --random_state 42
```

**Main Parameters**:

* `--fasta_folder`: Folder containing RF*.fasta files (required)
* `--model_type`: Model type, default rna
* `--device`: Compute device
* `--batch_size`: Batch size, default 16
* `--output`: Output image path (supports .png, .jpg, .pdf)
* `--n_components`: t-SNE dimension, default 2
* `--random_state`: Random seed, default 42

---

### 4. classify - Train RNA family classifier

**Function**: Train a classifier to assign RNA sequences into RNA families. Requires training.

**Basic Usage**:

```bash
# Basic usage (default parameters)
ReRNAFM classify --fasta_folder /path/to/fasta/folder

# Full parameter example
ReRNAFM classify \
    --fasta_folder /path/to/fasta/folder \
    --checkpoint_path my_classifier.pt \
    --model_type rna \
    --device cuda \
    --batch_size 16 \
    --train_batch_size 64 \
    --test_size 0.2 \
    --val_size 0.2 \
    --seed 42 \
    --num_epochs 100 \
    --lr 0.001 \
    --display_step 10
```

**Main Parameters**:

* `--fasta_folder`: FASTA folder path (required)
* `--checkpoint_path`: Model save path, default rna_family_classifier.pt
* `--model_type`: Model type, default rna
* `--device`: Compute device (cuda recommended)
* `--batch_size`: Embedding batch size, default 16
* `--train_batch_size`: Training batch size, default 32
* `--test_size`: Test set ratio, default 0.2
* `--val_size`: Validation set ratio, default 0.2
* `--num_epochs`: Number of epochs, default 50
* `--lr`: Learning rate, default 1e-3
* `--display_step`: Logging interval, default 10

---

### 5. predict_expression - Train mRNA expression predictor

**Function**: Train a binary classifier to predict mRNA expression levels (high/low). Requires training.

**Basic Usage**:

```bash
# Basic usage
ReRNAFM predict_expression --data_file expression_data.csv

# Full parameter example
ReRNAFM predict_expression \
    --data_file expression_data.csv \
    --checkpoint_path expression_model.pt \
    --model_type mrna \
    --device cuda \
    --batch_size 16 \
    --train_batch_size 64 \
    --value_0 0 \
    --value_2 2 \
    --test_size 0.2 \
    --val_size 0.2 \
    --num_epochs 100 \
    --lr 0.001 \
    --display_step 10
```

**Main Parameters**:

* `--data_file`: CSV file path (required), must include Sequence and Value columns
* `--checkpoint_path`: Model save path, default mrna_expression_classifier.pt
* `--model_type`: Model type, default mrna
* `--value_0`: Low expression value, default 0
* `--value_2`: High expression value, default 2
* Other parameters same as classify

**CSV Format**:

```csv
Sequence,Value,splits
GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU,0,train
AUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGC,2,val
...
```

---

## Installation and Usage

### Method 1: Run as Python script

```bash
# Run directly
python main.py embed --sequences "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU"

# Or use ReRNAFM script
./ReRNAFM embed --sequences "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU"
```

### Method 2: Install as system command (recommended)

```bash
# Install
pip install -e .

# Then use directly
ReRNAFM embed --sequences "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU"
```

---

## Image Output Notes

All visualization functions support saving images:

1. **predict_ss**: use `--output` for smart output (directory mode auto-generates .png and .ct)
2. **cluster**: saves t-SNE visualization
3. **classify**: saves training history plots (loss_history.png, accuracy_history.png)
4. **predict_expression**: saves training history plots

**Note**: If no output path is specified, images will try to display on screen (requires GUI). On servers, always specify output path.

## Notes

1. **No training required**: `embed`, `predict_ss`, `cluster`
2. **Training required**: `classify`, `predict_expression`
3. **GPU recommended**: use `--device cuda` for faster training
4. **Data format**: ensure correct FASTA format (RF*.fasta naming)
5. **Memory management**: reduce `--batch_size` if OOM occurs
6. **Image saving**: always specify `--output` on headless servers
7. **Smart output**: `predict_ss` auto-generates outputs using sequence IDs
