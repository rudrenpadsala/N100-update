import pandas as pd

from src.etl.normaliser import normalize_dataframe

df = pd.DataFrame({

    "year": [

        "FY2022",
        "2023",
        "2024*"

    ]

})

print(normalize_dataframe(df))