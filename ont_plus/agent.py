from google.adk.agents import Agent
from google.adk.tools import google_search, load_memory
from google.adk.tools.agent_tool import AgentTool
from .dorado_agent import dorado_agent
from .modkit_agent import modkit_agent
from .transcriptome_agent import transcriptome_agent
from google.adk.apps.app import App
from google.adk.agents.context_cache_config import ContextCacheConfig
from .execution import code_execute
from .rna_fm_agnet import rnafm_agent
from .scientific_agent import scientist_agent
from .gtex import gtex_agent
from .modomics import modomics_agent
from .signal_agent import signal_agent  

import requests
import re
import time

def ncbi_blast_tool(sequence, program="blastn", database="nt"):
    """
    Performs a remote NCBI BLAST search without local dependencies.
    
    Args:
        sequence (str): The DNA/RNA or Protein sequence.
        program (str): 'blastn' for nucleotides, 'blastp' for proteins.
        database (str): NCBI database (e.g., 'nt', 'nr', 'swissprot').
        
    Returns:
        str: Tabular results of the top hits or an error message.
    """
    base_url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
    
    # 1. Submit the Request (PUT)
    put_params = {
        "CMD": "Put",
        "PROGRAM": program,
        "DATABASE": database,
        "QUERY": sequence,
    }
    
    try:
        response = requests.get(base_url, params=put_params, timeout=30)
        # Extract Request ID (RID) using Regex
        rid_match = re.search(r'RID = (\w+)', response.text)
        if not rid_match:
            return "Error: Could not retrieve Request ID (RID) from NCBI."
        
        rid = rid_match.group(1)
        print(f"[*] Task submitted. RID: {rid}")

        # 2. Poll for Status (CHECK)
        while True:
            check_params = {"CMD": "Get", "FORMAT_OBJECT": "SearchInfo", "RID": rid}
            check_res = requests.get(base_url, params=check_params, timeout=30)
            
            if "Status=WAITING" in check_res.text:
                print("[...] Search in progress, waiting 20 seconds...")
                time.sleep(20)
            elif "Status=READY" in check_res.text:
                if "ThereAreHits=yes" in check_res.text:
                    print("[!] Success: Hits found. Fetching data...")
                    break
                else:
                    return "Search complete: No hits found."
            else:
                return "Error: Unexpected status or task timeout."

        # 3. Retrieve Results (GET)
        # Tabular format (FORMAT_TYPE=Tabular) is easiest for Agents to parse
        get_params = {
            "CMD": "Get",
            "RID": rid,
            "FORMAT_TYPE": "Text", 
        }
        final_res = requests.get(base_url, params=get_params, timeout=30)
        
        # Clean output: Remove comment lines (starting with #) for the Agent
        data_lines = [line for line in final_res.text.splitlines() if not line.startswith("#")]
        return "\n".join(data_lines) if data_lines else "No tabular data returned."

    except requests.exceptions.RequestException as e:
        return f"Network Error: {str(e)}"




search_agent = Agent(
    name="SearchAgent",
    model="gemini-2.5-flash",
    instruction="You are the search agent of the Dorado/Modkit/transcriptome agent. You are responsible for searching the internet for information. Also, based on the internet information, you should double check the code.",
    tools=[google_search]
)

nanopore_root_agent = Agent(
    name="RootAgent",
    model="gemini-3.1-flash-lite-preview",
    instruction=(
        "You are the Orchestrator for the Nanopore Analysis System. Your primary goal is to route user requests and ensure safe execution.\n\n"
        "### Routing Logic:\n"
        "- Dorado: Use `DoradoRootAgent` for basecalling/demultiplexing. If modifications are mentioned, suggest `modkit` for downstream analysis.\n"
        "- Modkit: Use `ModkitRootAgent` ONLY after the Dorado command is finalized or if analyzing existing BAMs.\n"
        "- Transcriptome: Use `TranscriptomeAgent` for specialized RNA analysis including mRNA quantification, gene fusion detection and de novo transcriptome assembly. \n"
        "- GTEx: Use `GTEXAgent` to analyze the GTEx  tissue expression and isoform usage and significance of the transcripts compared with healthy tissue (GTEx data). Please use gene_symbol first and find the ensembl id in that agent.\n"
        "- RNAFM: Use `RNAFMAgent` for specialized RNA analysis including RNA embedding, secondary structure prediction, clustering, classification, and expression prediction.\n"
        "- Interpretation/Search for Papaers in PMCMed: Use `ScientistAgent`. \n"
        "- Search: Use `SearchAgent` to verify syntax or look up documentation.\n\n"
        "- Execute: Use `code_execute` to execute the command. If the command is not executable, ask `search_agent` for help.\n"
        "- Sequence Analysis: Use `ncbi_blast_tool` to analyze the DNA/RNA/Protein sequence."
        "- Modomics: Use `ModomicsAgent` to answer the user's questions based on modomics Database. The base url is the base URL: https://genesilico.pl/modomics/."
        "- Signal Plotting: Use `SignalAgent` to plot the signal of the Nanopore sequencing signal."
        "### Execution & Safety Rules:\n"
        "1. PLACEHOLDERS: Before executing code, identify any [PLACEHOLDER_PATHS] and ask the user to provide the actual values.\n"
        "2. FILE SAFETY: If a command involves `rm` (deletion) or overwriting files, you MUST ask: 'Are you sure you want to delete/overwrite [file path]?' before proceeding.\n"
        "3. ERROR HANDLING: If `code_execute` returns an error, analyze it and suggest specific fixes or ask `search_agent` for help.\n"
        "4. STATE MANAGEMENT: After a Dorado command is generated, ask: 'Is this Dorado command complete?' If yes, proceed to Modkit if relevant. If no, stay with `dorado_agent`.\n\n"
        "### Environment Paths:\n"
        "- Dorado: singularity exec ./singularity/bot.sif dorado\n"
        "- Modkit: singularity exec ./singularity/bot.sif modkit\n"
        "- RNAFM: singularity exec -B ./Reconstruction_RNAFM/:/Reconstruction_RNAFM ./singularity/bot.sif mamba run -n RNA_FM /Reconstruction_RNAFM/ReRNAFM For the inputs please mount the directory to the container.\n"
        "- stringtie: singularity exec ./singularity/bot.sif stringtie"
        "- flair : singularity exec ./singularity/bot.sif /opt/conda/envs/flair/bin/flair"
        "- Dependencies: use 'ml samtools', ml bedtools and 'ml R' and use && to concat the command. Please use R to draw plots (do not use singularity container to execute R commands and do not use any other libraries)."
        "If you need use singularity container to execute some commands, please ask for permission first."
    ),
    tools=[AgentTool(agent=dorado_agent), AgentTool(agent=modkit_agent), AgentTool(agent=transcriptome_agent), AgentTool(agent=gtex_agent), AgentTool(agent=modomics_agent),
           AgentTool(agent=search_agent), AgentTool(agent=rnafm_agent), AgentTool(agent=scientist_agent), AgentTool(agent=signal_agent), code_execute, ncbi_blast_tool]
)

# Create the app with context caching configuration
app = App(
    name='ont_plus',
    root_agent=nanopore_root_agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=4096,    # Minimum tokens to trigger caching
        ttl_seconds=600,    # Store for up to 10 minutes
        cache_intervals=10,  # Refresh after 5 uses
    ),
)

