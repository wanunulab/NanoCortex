import requests

def pmc_search_tool(keyword_query, max_results=5):
    """
    Search PubMed Central (PMC) for literature based on keywords.
    
    Args:
        keyword_query (str): The search terms (e.g., "Agentic AI AND spatial transcriptomics").
        max_results (int): Number of articles to retrieve (default: 5).
        
    Returns:
        list: A list of dictionaries containing article metadata.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # --- Step 1: Search for Article IDs (ESearch) ---
    search_url = f"{base_url}esearch.fcgi"
    search_params = {
        "db": "pmc",            # Target the PMC database (free full-text)
        "term": keyword_query,  # Your search keywords
        "retmode": "json",      # Return results in JSON format
        "retmax": max_results   # Limit the number of results
    }
    
    try:
        search_res = requests.get(search_url, params=search_params, timeout=10)
        search_data = search_res.json()
        
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return "No articles found for the given keywords."
            
        print(f"[*] Found {len(id_list)} articles. Fetching details...")

        # --- Step 2: Fetch Article Metadata (ESummary) ---
        summary_url = f"{base_url}esummary.fcgi"
        summary_params = {
            "db": "pmc",
            "id": ",".join(id_list), # Join IDs with commas
            "retmode": "json"
        }
        
        summary_res = requests.get(summary_url, params=summary_params, timeout=10)
        summary_data = summary_res.json()
        
        articles = []
        result_dict = summary_data.get("result", {})
        
        # Parse the JSON response into a clean list of dictionaries for the Agent
        for pmc_id in id_list:
            if pmc_id in result_dict:
                article_info = result_dict[pmc_id]
                clean_article = {
                    "PMC_ID": pmc_id,
                    "Title": article_info.get("title", ""),
                    "Journal": article_info.get("fulljournalname", ""),
                    "PubDate": article_info.get("pubdate", ""),
                    "Authors": [auth.get("name") for auth in article_info.get("authors", [])],
                    "DOI": article_info.get("articleids", [{}])[0].get("value", "") # Attempt to get DOI
                }
                articles.append(clean_article)
                
        return articles

    except requests.exceptions.RequestException as e:
        return f"Network Error: {str(e)}"


def get_pmc_fulltext_tool(pmc_id):
    """
    Full-text retrieval tool optimized for Agents.
    Inputs a PMC ID and returns the cleaned, section-formatted full text.
    
    Args:
        pmc_id (str): e.g., "PMC10345678" or just "10345678"
    """
    # Ensure ID has "PMC" prefix
    pmc_id = str(pmc_id).upper()
    if not pmc_id.startswith("PMC"):
        pmc_id = f"PMC{pmc_id}"
        
    # Call NCBI BioC API designed for text mining
    url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmc_id}/unicode"
    
    try:
        print(f"[*] Attempting to fetch full text for {pmc_id}...")
        response = requests.get(url, timeout=15)
        
        if response.status_code == 404:
            return f"Error: Full text for {pmc_id} not found. The article might not be in the Open Access (OA) subset."
        elif response.status_code != 200:
            return f"Error: API request failed with status code {response.status_code}"
            
        data = response.json()
        
        # Parse JSON, extract clean text, and label sections
        full_text_blocks = []
        for document in data.get("documents", []):
            for passage in document.get("passages", []):
                # Get the section type of the passage (e.g., ABSTRACT, INTRO, METHODS)
                section = passage.get("infons", {}).get("section_type", "UNKNOWN")
                text = passage.get("text", "").strip()
                
                if text:
                    # Format text so LLM knows which section it belongs to
                    full_text_blocks.append(f"### {section.upper()} ###\n{text}")
                    
        clean_full_text = "\n\n".join(full_text_blocks)
        
        if not clean_full_text:
            return "Warning: Connection successful, but no valid text content parsed."
            
        return clean_full_text

    except requests.exceptions.RequestException as e:
        return f"Network Error: {str(e)}"
    except ValueError:
        return "Error: Returned data is not valid JSON."
