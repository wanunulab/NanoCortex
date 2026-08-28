#!/usr/bin/env python3
import argparse
import logging
import sys

# Import core libraries
import pod5
import remora
from remora import io, refine_signal_map

# Ensure the custom module 'newio' is accessible in the python path
try:
    import newio
except ImportError:
    print("Error: Could not find custom module 'newio'. Please ensure the file is in the current directory.")
    sys.exit(1)

# Silence Remora DEBUG messages for cleaner output
logging.getLogger("Remora").setLevel(logging.INFO)

def load_data(kmer_table, mod_pod5, mod_bam, can_pod5, can_bam):
    """Initializes data readers for POD5 and BAM files."""
    mod_pod5_dr = pod5.DatasetReader(mod_pod5)
    can_pod5_dr = pod5.DatasetReader(can_pod5)
    can_bam_fh = io.ReadIndexedBam(can_bam)
    mod_bam_fh = io.ReadIndexedBam(mod_bam)
    return kmer_table, mod_pod5_dr, mod_bam_fh, can_pod5_dr, can_bam_fh

def region_info(chr_name, strand, start, end):
    """Creates a Remora RefRegion object."""
    return io.RefRegion(ctg=chr_name, strand=strand, start=start, end=end)

def main():
    parser = argparse.ArgumentParser(description="Remora Signal Comparison and Plotting CLI Tool")

    # --- Required Input Files ---
    group_input = parser.add_argument_group('Input Files')
    group_input.add_argument("--kmer_table", required=True, 
                             help="Path to k-mer model file used for signal rescaling.")
    group_input.add_argument("--mod_pod5", required=True, 
                             help="POD5 file or directory for the Modified sample.")
    group_input.add_argument("--mod_bam", required=True, 
                             help="Indexed BAM file for the Modified sample.")
    group_input.add_argument("--can_pod5", required=True, 
                             help="POD5 file or directory for the Canonical (control) sample.")
    group_input.add_argument("--can_bam", required=True, 
                             help="Indexed BAM file for the Canonical sample.")

    # --- Required Genomic Region ---
    group_region = parser.add_argument_group('Genomic Region')
    group_region.add_argument("--chr", required=True, 
                             help="Chromosome name (e.g., chr1).")
    group_region.add_argument("--strand", required=True, choices=["+", "-"], 
                             help="Genomic strand: '+' or '-'.")
    group_region.add_argument("--start", type=int, required=True, 
                             help="Start coordinate (0-based).")
    group_region.add_argument("--end", type=int, required=True, 
                             help="End coordinate (0-based).")

    # --- Output & Plotting Configuration ---
    group_out = parser.add_argument_group('Output & Plotting Options')
    group_out.add_argument("--save_path", required=True, 
                             help="Output path for the plot (e.g., plot.pdf or plot.png).")
    group_out.add_argument("--max_reads", type=int, default=100, 
                             help="Maximum number of reads to plot per sample (Default: 100).")
    group_out.add_argument("--ylim_min", type=float, default=-3.0, 
                             help="Minimum value for the Y-axis (Default: -3.0).")
    group_out.add_argument("--ylim_max", type=float, default=3.0, 
                             help="Maximum value for the Y-axis (Default: 3.0).")

    args = parser.parse_args()

    # Execute core logic
    # try:
    # Load data handles
    _, mod_pod5_dr, mod_bam_fh, can_pod5_dr, can_bam_fh = load_data(
        args.kmer_table, args.mod_pod5, args.mod_bam, args.can_pod5, args.can_bam
    )

    # Define genomic region
    ref_reg = region_info(args.chr, args.strand, args.start, args.end)

    # Initialize signal map refiner
    sig_map_refiner = refine_signal_map.SigMapRefiner(
        kmer_model_filename=args.kmer_table,
        do_rough_rescale=True,
        scale_iters=0,
        do_fix_guage=True,
    )

    # Generate plot via newio module
    newio.plot_signal_at_ref_region(
        ref_reg=ref_reg,
        pod5_bam_pairs=[(mod_pod5_dr, mod_bam_fh), (can_pod5_dr, can_bam_fh)],
        save_data_path=args.save_path,
        sig_map_refiner=sig_map_refiner,
        max_reads=args.max_reads,
        reverse_signal=True,
        sample_names=["mod", "can"],
        sample_colors=["#5cc2a7", "#ff9933"],  # Teal for mod, Orange for can
        mean_line_colors=["#216e54", "#c95e0c"], # Darker shades for mean lines
        ylim=(args.ylim_min, args.ylim_max),
        ref_mod=None,
    )
    print(f"Success! Plot saved to: {args.save_path}")

    # except Exception as e:
    #     print(f"Runtime Error: {e}")
    #     sys.exit(1)

if __name__ == "__main__":
    main()