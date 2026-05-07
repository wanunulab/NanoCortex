import torch
import pysam
import gffutils
import os
from tqdm import tqdm
import multimolecule
from transformers import pipeline

def get_labels(chrom, start, end, strand, db):
    """Generates three-class labels for genomic coordinates.

    Labels are assigned based on the relative position of exons within the specified
    genomic range and the strand orientation.

    Args:
        chrom (str): Chromosome name.
        start (int): Start coordinate (0-based).
        end (int): End coordinate (0-based).
        strand (str): Strand orientation ('+' or '-').
        db (gffutils.FeatureDB): Genomic annotation database.

    Returns:
        torch.Tensor: A LongTensor of shape (end - start,) containing labels:
            0: None (non-splice site)
            1: Acceptor (AG)
            2: Donor (GT/GU)
    """
    length = end - start
    labels = torch.zeros(length, dtype=torch.long)
    
    # Find all exons within this region
    # Use region parameter for spatial index query
    for exon in db.region(region=(chrom, start, end),strand = strand ,featuretype = 'exon'):
        # Calculate index relative to window start position (0-based)
        rel_start = exon.start - start
        rel_end = exon.end - start - 1 
        
        if strand == '+':
            # Positive strand: exon start is Acceptor (1), end is Donor (2)
            if 0 <= rel_start < length:
                labels[rel_start] = 1
            if 0 <= rel_end < length:
                labels[rel_end] = 2
        else:
            # Negative strand: in genomic coordinates, larger coordinate is Acceptor (1), smaller is Donor (2)
            if 0 <= rel_end < length:
                labels[rel_end] = 1
            if 0 <= rel_start < length:
                labels[rel_start] = 2
    return labels

def create_training_dataset(fasta_path, gtf_path, output_dir, window_size=1024):
    """Extracts sequence strings and splicing labels to create a training dataset.

    This function iterates through genes in the annotation, samples windows,
    extracts the corresponding genomic sequences, and generates splicing labels.
    The resulting data is saved as PyTorch .pt files.

    Args:
        fasta_path (str): Path to the genome FASTA file.
        gtf_path (str): Path to the GTF/GFF annotation file.
        output_dir (str): Directory to save the generated dataset.
        window_size (int, optional): Size of the sampling window. Defaults to 1024.

    Returns:
        None
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load genome FASTA
    genome = pysam.FastaFile(fasta_path)
    
    # Parse GTF/GFF
    db_path = gtf_path + ".db"
    if not os.path.exists(db_path):
        print("Creating genome annotation database, please wait...")
        # Disable infer functions to speed up processing and keep original structure
        db = gffutils.create_db(gtf_path, db_path, force=True, 
                                disable_infer_genes=True, 
                                disable_infer_transcripts=True,
                                merge_strategy='create_unique')
    else:
        db = gffutils.FeatureDB(db_path)

    print("Starting data extraction...")
    sample_idx = 0
    seq_list = []
    label_list = []
    # Iterate through all genes
    for gene in tqdm(db.features_of_type('gene')):
        chrom = gene.chrom
        gene_len = gene.end - gene.start
        
        # Determine sampling windows
        if gene_len < window_size:
            # If gene length is less than window size, take one window centered on the gene
            center = (gene.start + gene.end) // 2
            start = center - window_size // 2
            end = start + window_size
            windows = [(start, end)]
        else:
            # Otherwise, use sliding window sampling with 50% overlap
            windows = []
            for s in range(gene.start, gene.end - window_size, window_size // 2):
                windows.append((s, s + window_size))

        for w_start, w_end in windows:
            try:
                # 1. Extract raw nucleotide sequence string
                seq = genome.fetch(chrom, w_start, w_end).upper()
                if len(seq) != window_size:
                    continue
                
                # 2. Generate label tensor
                labels = get_labels(chrom, w_start, w_end, gene.strand, db)
                
                # 3. Filtering logic: only keep windows containing splicing sites (optional)
                if labels.sum() == 0:
                    continue
                
                # 4. Save data
                # Save 'seq' string directly, decide how to encode during training
                seq_list.append(seq)
                label_list.append(labels)
                
                sample_idx += 1

                if sample_idx > 500: return seq_list, label_list

            except Exception:
                continue

    print(f"Data preparation complete! Total samples generated: {sample_idx}. Stored in: {output_dir}")

if __name__ == "__main__":
    # Configure paths
    seq_list, label_list = create_training_dataset(
        fasta_path="/athena/chenlab/scratch/ziw4007/Chen_hPSC/reference/chm13v2.0.fa", 
        gtf_path="/athena/chenlab/scratch/ziw4007/Chen_hPSC/reference/chm13.draft_v2.0.gene_annotation.gff3", 
        output_dir="/athena/chenlab/scratch/ziw4007/llm/ONT_plus/ont_plus/splice_raw_dataset",
        window_size=1024
    )
    seq_list
