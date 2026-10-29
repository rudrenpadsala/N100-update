import yfinance as yf

for cid, sym in [('M&M', 'M&M.NS'), ('TATAMOTORS', 'TMCV.NS'), ('LTIM', 'LTM.NS')]:
    df = yf.download(sym, start='2025-01-01', progress=False)
    print(f"{cid} ({sym}): {len(df)} days, Latest: {df.index[-1].strftime('%Y-%m-%d')}, Close: {df['Close'].iloc[-1].item():.2f}")
