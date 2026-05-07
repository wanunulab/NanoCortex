import requests
import pandas as pd
import sys
from scipy.stats import binomtest

from google.adk.agents import Agent
from google.adk.tools import google_search

# Constants
GTEX_BASE_URL = "https://gtexportal.org/api/v2"
ENSEMBL_REST_URL = "https://rest.ensembl.org"

def get_isoform_usage_percentage(tissue_id: str, transcript_id: str, gene_id : str) -> float:
    """
    Calculates the usage percentage of a specific isoform in a specific tissue.
    
    Args:
        tissue_id (str): The GTEx Tissue Site Detail ID (e.g., "Adrenal_Gland").
        transcript_id (str): The Ensembl Transcript ID (e.g., "ENST00000335181.9").
        gene_id (str): The Ensembl Gene ID corresponding to the transcript (e.g., "ENSG00000123415").
   
    Returns:
        float: The usage percentage (0-100). Returns -1.0 if error occurs.
    """
    
    # 1. Resolve Gene ID from Transcript ID (using Ensembl API)
    # Strip version for lookup
    transcript_base = transcript_id.split('.')[0]

    # 2. Fetch GTEx Expression Data for the Gene
    endpoint = f"{GTEX_BASE_URL}/expression/medianTranscriptExpression"
    params = {
        "datasetId": "gtex_v10",
        "gencodeId": gene_id,
        "tissueSiteDetailId" : tissue_id,
        "format": "json",
    }
    gtex_gene_id = gene_id
    try:
        resp = requests.get(endpoint, params=params)
        resp.raise_for_status()
        
        json_resp = resp.json()
        # Handle API response structure variations
        if 'medianTranscriptExpression' in json_resp:
             data = json_resp['medianTranscriptExpression']
        elif 'data' in json_resp:
             data = json_resp['data']
        else:
             data = []
        
        if not data:
            print(f"Error: No expression data found in GTEx for gene {gtex_gene_id}")
            return -1.0
            
    except Exception as e:
        print(f"Error connecting to GTEx API: {e}")
        return -1.0
        
    # 4. Process Data with Pandas
    df = pd.DataFrame(data)
    
    # Filter for the specific tissue
    tissue_df = df[df['tissueSiteDetailId'] == tissue_id].copy()
    
    if tissue_df.empty:
        print(f"Error: Tissue '{tissue_id}' not found for gene {gtex_gene_id}")
        return -1.0
        
    # Calculate Total Gene Expression in this tissue
    total_tpm = tissue_df['median'].sum()
    
    if total_tpm == 0:
        return 0.0
        
    # Find the specific transcript's expression
    # Handle potential version differences in GTEx data
    tissue_df['transcript_base'] = tissue_df['transcriptId'].apply(lambda x: x.split('.')[0])
    
    target_row = tissue_df[tissue_df['transcript_base'] == transcript_base]
    
    if target_row.empty:
        print(f"Error: Transcript {transcript_id} not found in GTEx data for {tissue_id}")
        return 0.0
        
    # There should only be one match per tissue per transcript
    target_tpm = target_row['median'].sum()
    
    usage_percentage = (target_tpm / total_tpm) * 100
    
    return usage_percentage

def get_isoform_tpm(gene_id: str ,transcript_id: str, tissue_id: str) -> float:
    """
    Retrieve the median TPM value of a specific transcript (isoform) in a particular tissue from GTEx.

    Args:
        gene_id (str): The Gencode/Ensembl Gene ID corresponding to the transcript, e.g., 'ENSG00000123415'
        transcript_id (str): The versioned transcript/isoform ID, e.g., 'ENST00000331789.8'
        tissue_id (str): The GTEx tissueSiteDetailId, e.g., 'Brain_Cortex'
   

    Returns:
        float: Median TPM expression value for the isoform in the given tissue, or -1.0 if not found/error.
    """

    try:
        endpoint = f"{GTEX_BASE_URL}/expression/medianTranscriptExpression"
        params = {
            "datasetId": "gtex_v10",
            "gencodeId": gene_id,
            "tissueSiteDetailId" : tissue_id,
            "format": "json",
        }
        resp = requests.get(endpoint, params=params)
        if resp.status_code != 200:
            print(f"Error: Failed to query GTEx API (status {resp.status_code})")
            return -1.0

        json_resp = resp.json()
        # API may respond in different formats
        if 'medianTranscriptExpression' in json_resp:
            data = json_resp['medianTranscriptExpression']
        elif 'data' in json_resp:
            data = json_resp['data']
        else:
            data = []

        if not data:
            print(f"Error: No expression data found in GTEx for gene")
            return -1.0

        df = pd.DataFrame(data)
        # Correct filter logic: use & for elementwise comparisons and parenthesis for clarity
        tissue_df = df[(df['tissueSiteDetailId'] == tissue_id) & (df['transcriptId'] == transcript_id)]
        if tissue_df.empty:
            print(f"Error: Tissue '{tissue_id}' not found for transcript {transcript_id}")
            return -1.0

        # Usually only one row per transcript/tissue
        median_tpm = tissue_df['median'].sum()
        return float(median_tpm)
    except Exception as e:
        print(f"Error connecting to GTEx API: {e}")
        return -1.0



def isoform_significance_test(observed_m, total_n, gtex_usage_fraction) -> dict:
    """
    Calculates the significance of a specific isoform in a specific tissue.
    
    Args:
        observed_m (int): The number of observed reads or counts for the isoform.
        total_n (int): The total observed gene counts (all isoforms).
        gtex_usage_fraction (float): The GTEx baseline usage fraction for the isoform (between 0 and 1).
        
    Returns:
        dict: A dictionary containing the usage percentage, baseline ratio, fold change, p-value, and strategic insight.
    """
    # Run Binomial Test
    result = binomtest(observed_m, n=total_n, p=gtex_usage_fraction)
    
    p_value = result.pvalue
    observed_ratio = observed_m / total_n
    fold_change = observed_ratio / (gtex_usage_fraction + 1e-9)
    
    return {
        "observed_ratio": f"{observed_ratio:.2%}",
        "baseline_ratio": f"{gtex_usage_fraction:.2%}",
        "fold_change": round(fold_change, 2),
        "p_value": p_value,
        "is_significant": p_value < 0.05,
        "strategic_insight": "Upregulated Variant" if fold_change > 1 else "Downregulated Variant"
    }



def get_all_isoforms_metadata(gencode_id: str) -> list:
    """
    Retrieves all known reference transcripts (isoforms) for a specific gene.
    Returns metadata including transcript ID, biotype, and genomic coordinates.
    
    Args:
        gencode_id (str): The versioned Gencode ID (e.g., 'ENSG00000026508.19')

    Returns:
        list: A list of transcript isoform IDs.
    """
    # GTEx API v2 Reference Endpoint
    url = "https://gtexportal.org/api/v2/reference/transcript"
    
    params = {
        "gencodeId": gencode_id,
        "datasetId": "gtex_v10",
        "format": "json",
        "gencodeVersion" : "v39"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        if not data:
            print(f"No isoforms found for {gencode_id}.")
            return []
        
        # Extract all transcript isoform IDs as a list
        isoform_ids = [item['transcriptId'] for item in data if 'transcriptId' in item]
        return isoform_ids
        
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return []

def get_gene(gene_symbol: str) -> str:
    """
    Fetches the Gencode gene ID for a given gene symbol using the GTEx API.

    Args:
        gene_symbol (str): The gene symbol (e.g., 'BRCA1' or 'TP53').

    Returns:
        str: The Gencode gene ID as a string, or an empty string if not found or on error.
    """
    url = "https://gtexportal.org/api/v2/reference/gene"
    params = {
        "geneId": gene_symbol,
        "gencodeVersion": "v39"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get('data', [])

        if not data:
            print(f"No gene found for {gene_symbol}.")
            return ""

        gencode_id = data[0].get('gencodeId', "")
        return gencode_id

    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return ""


gtex_agent = Agent(
    name="GTEXAgent",
    model="gemini-2.5-flash",
    instruction="""You are a GTEX agent.
    You are responsible for using GTEx data to analyze the isoform usage and significance.
    You should use the get_isoform_usage_percentage tool to get the isoform usage percentage.
    You should use the isoform_significance_test tool to get the isoform significance.
    You should use the get_all_isoforms_metadata tool to get the all isoforms metadata.
    You should use the get_gene tool to find the correct Gencode ID.
    You should use the get_isoform_tpm to get the tpm for each isoform.
    For all gene id realted things use get_gene to determine the Gencode ID.
    If you have RefSeq transcript id, please find the genecode transcript id in ./gencode.v39.metadata.RefSeq.
    GTEx data is about healthy tissue for all human. If you need to find the parameters for the tools including the tissue name, transcript id, gene id, etc, 
    """,  
    description = ("When you want to see whether some disease related genes have differential isoform usage compared with healthy tissue, you should use this agent to analyze the isoform usage and significance"),
    tools=[get_isoform_usage_percentage, isoform_significance_test, get_all_isoforms_metadata, get_gene,get_isoform_tpm]
)


