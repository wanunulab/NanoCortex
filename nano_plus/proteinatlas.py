import requests

# 查询某个基因（如 EGFR）在各组织的蛋白表达水平
search_url = "https://www.proteinatlas.org/api/search_download.php"
params = {
    "search": "EGFR",
    "format": "json",
    "columns": "g,gs,ptia", # g: ID, gs: Symbol, ptia: 蛋白组织关联数据
    "compress": "no"
}

response = requests.get(search_url, params=params)
if response.status_code == 200:
    results = response.json()
    # print(results[0])
    for entry in results:
        print(entry)
        # ptia 字段通常包含组织名和对应的表达等级
        print(f"Gene: {entry['Gene synonym']}, Protein Data: {entry.get('Protein tissue association', 'N/A')}")