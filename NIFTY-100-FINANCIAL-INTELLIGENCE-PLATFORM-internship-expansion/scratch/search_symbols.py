import requests

def search_yf(query):
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    data = r.json()
    print(f"Results for '{query}':")
    for item in data.get('quotes', [])[:5]:
        print(f"  {item.get('symbol')} | {item.get('shortname')} | {item.get('exchDisp')}")

search_yf("Tata Motors")
search_yf("LTIMindtree")
