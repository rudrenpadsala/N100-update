import requests

headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get("https://query2.finance.yahoo.com/v1/finance/search?q=INE214T01019", headers=headers)
print("ISIN INE214T01019:", r.json())

# Also search for 'L&T Infotech' or 'Larsen'
r2 = requests.get("https://query2.finance.yahoo.com/v1/finance/search?q=L&T+Infotech", headers=headers)
print("L&T Infotech:", r2.json())
