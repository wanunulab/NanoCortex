import pysam
import pandas as pd
import gffutils
import os

def scan_splicing_mutations(vcf_file, bam_file, gtf_file, window=5):
    """
    扫描所有落在剪接位点附近并引起剪接比例变化的基因
    Scan all genes lying near splice sites that cause changes in splicing ratios.
    """
    samfile = pysam.AlignmentFile(bam_file, "rb")
    vcf = pysam.VariantFile(vcf_file)
    
    # 加载或创建 gffutils 数据库
    db = get_or_create_db(gtf_file)
    
    results = []

    for record in vcf:
        chrom = record.chrom
        pos = record.pos  # VCF position is 1-based
        
        # 1. 检查突变是否在剪接点窗口内 (Check if mutation is near a splice site)
        is_splice, gene_name = check_splice_site_and_gene(db, chrom, pos, window)
        
        if is_splice:
            # 2. 获取该位点周围的剪接证据 (Get splicing evidence around the site)
            evidence = get_junction_metrics(samfile, chrom, pos)
            
            # 3. 判定阈值：如果 split reads 占比显著（例如 > 10%）
            if evidence['split_ratio'] > 0.1:
                results.append({
                    "gene": gene_name,
                    "location": f"{chrom}:{pos}",
                    "ref_alt": f"{record.ref}>{record.alts[0]}",
                    "split_ratio": evidence['split_ratio'],
                    "depth": evidence['depth'],
                    "type": "Potential Splice Site Mutation"
                })

    return pd.DataFrame(results)

def get_or_create_db(gtf_path):
    """
    Load a gffutils database from a GTF file. 
    Creates a .db file if it doesn't exist.
    """
    db_path = gtf_path + ".db"
    if not os.path.isfile(db_path):
        print(f"Creating gffutils database for {gtf_path}...")
        # Create DB (this might take some time for large GTFs)
        db = gffutils.create_db(
            gtf_path, 
            dbfile=db_path, 
            force=False, 
            keep_order=True, 
            merge_strategy='merge', 
            sort_attribute_values=True,
            disable_infer_genes=True, 
            disable_infer_transcripts=True
        )
    else:
        db = gffutils.FeatureDB(db_path)
    return db

def check_splice_site_and_gene(db, chrom, pos, window):
    """
    Check if the position is within `window` bp of an exon boundary.
    Returns (bool, gene_name).
    """
    # gffutils uses 1-based coordinates
    start = pos - window
    end = pos + window
    
    is_near = False
    gene_name = "Unknown"
    
    try:
        # Fetch exons overlapping the window
        features = db.region(seqid=chrom, start=start, end=end, featuretype='exon')
        
        for feature in features:
            # Check distance to boundaries (start and end are 1-based inclusive)
            dist_start = abs(feature.start - pos)
            dist_end = abs(feature.end - pos)
            
            if dist_start <= window or dist_end <= window:
                is_near = True
                # Extract gene name
                if 'gene_name' in feature.attributes:
                    gene_name = feature.attributes['gene_name'][0]
                elif 'gene_id' in feature.attributes:
                    gene_name = feature.attributes['gene_id'][0]
                break
                
    except Exception:
        # Handle cases where chromosome is not in DB or other errors
        pass
        
    return is_near, gene_name

def get_junction_metrics(samfile, chrom, pos):
    """Count splicing reads (CIGAR contains N) around a specific position."""
    total_reads = 0
    split_reads = 0
    
    # Scan reads around 10bp of the position
    try:
        # pysam fetch uses 0-based coordinates, pos is 1-based
        for read in samfile.fetch(chrom, pos-10, pos+10):
            if read.is_unmapped or read.is_secondary:
                continue
            total_reads += 1
            # 'N' (operation code 3) in CIGAR represents skipped region, which is splicing
            if read.cigartuples and any(op[0] == 3 for op in read.cigartuples):
                split_reads += 1
    except ValueError:
        pass
            
    ratio = split_reads / total_reads if total_reads > 0 else 0
    return {"depth": total_reads, "split_ratio": ratio}
