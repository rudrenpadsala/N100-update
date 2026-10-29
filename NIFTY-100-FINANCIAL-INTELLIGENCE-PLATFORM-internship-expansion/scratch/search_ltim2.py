import requests

for q in ["Larsen Toubro Infotech", "Larsen & Toubro", "LTIMindtree Ltd"]:
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={q}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    data = r.json()
    print(f"Results for '{q}':")
    for item in data.get('quotes', [])[:5]:
        print(f"  {item.get('symbol')} | {item.get('shortname')} | {item.get('exchDisp')}")
