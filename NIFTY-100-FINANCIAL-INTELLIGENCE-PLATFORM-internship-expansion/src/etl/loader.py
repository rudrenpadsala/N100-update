"""
loader.py

Load Excel files, clean data,
insert into SQLite database,
generate load audit report.
"""


from pathlib import Path
import pandas as pd
import sqlite3
from datetime import datetime



# ==========================================================
# Project Paths
# ==========================================================


BASE_DIR = Path(__file__).resolve().parents[2]


RAW_DATA_PATH = BASE_DIR / "data" / "raw"


DB_PATH = BASE_DIR / "db" / "nifty100.db"


AUDIT_PATH = BASE_DIR / "data" / "load_audit.csv"



# ==========================================================
# Header Configuration
# ==========================================================


HEADER_ONE_FILES = {

    "analysis",
    "balancesheet",
    "cashflow",
    "companies",
    "documents",
    "profitandloss",
    "prosandcons",

}



# ==========================================================
# Excel Loader
# ==========================================================


def load_all_excel_files():


    datasets = {}


    excel_files = sorted(
        RAW_DATA_PATH.glob("*.xlsx")
    )


    print("=" * 70)
    print("Loading Excel Files")
    print("=" * 70)



    for file in excel_files:


        try:


            if file.stem in HEADER_ONE_FILES:

                df = pd.read_excel(
                    file,
                    header=1
                )

            else:

                df = pd.read_excel(file)



            # Remove empty rows

            df = df.dropna(
                how="all"
            )


            # Remove empty columns

            df = df.dropna(
                axis=1,
                how="all"
            )


            # Remove duplicates

            df = df.drop_duplicates()



            # Clean columns

            df.columns = (

                df.columns
                .astype(str)
                .str.strip()
                .str.replace(
                    "\n",
                    " ",
                    regex=False
                )

            )



            datasets[file.stem] = df



            print(
                f"✔ Loaded : {file.name}"
            )



        except Exception as e:


            print(
                f"❌ Error : {file.name}"
            )

            print(e)



    return datasets



# ==========================================================
# Excel -> SQLite Mapping
# ==========================================================


TABLE_MAPPING = {
    "companies": "companies",
    "analysis": "analysis",
    "balancesheet": "balancesheet",
    "cashflow": "cashflow",
    "documents": "documents",
    "financial_ratios": "financial_ratios",
    "market_cap": "market_cap",
    "peer_groups": "peer_groups",
    "profitandloss": "profitandloss",
    "prosandcons": "prosandcons",
    "sectors": "sectors",
    "stock_prices": "stock_prices",
}



# ==========================================================
# Load Into Database
# ==========================================================


def load_to_database(datasets):


    conn = sqlite3.connect(
        DB_PATH
    )


    audit = []



    print("\n")
    print("=" * 70)
    print("Loading Data Into SQLite")
    print("=" * 70)



    for excel_name, table_name in TABLE_MAPPING.items():



        try:


            if excel_name not in datasets:


                print(
                    f"⚠ Missing : {excel_name}"
                )

                continue



            df = datasets[excel_name]



            before = pd.read_sql(

                f"SELECT COUNT(*) as count FROM {table_name}",

                conn

            ).iloc[0]["count"]



            df.to_sql(

                table_name,

                conn,

                if_exists="append",

                index=False

            )



            after = pd.read_sql(

                f"SELECT COUNT(*) as count FROM {table_name}",

                conn

            ).iloc[0]["count"]



            inserted = after - before



            print(
                f"✔ {table_name} : {inserted} rows"
            )



            audit.append({

                "table": table_name,

                "rows_loaded": inserted,

                "status": "SUCCESS",

                "timestamp": datetime.now()

            })



        except Exception as e:



            print(
                f"❌ Failed : {table_name}"
            )

            print(e)



            audit.append({

                "table": table_name,

                "rows_loaded": 0,

                "status": "FAILED",

                "timestamp": datetime.now()

            })



    conn.commit()

    conn.close()



    audit_df = pd.DataFrame(audit)


    audit_df.to_csv(

        AUDIT_PATH,

        index=False

    )



    print("\nAudit created:")

    print(AUDIT_PATH)




# ==========================================================
# Summary
# ==========================================================


def show_summary(datasets):


    print("\n")
    print("=" * 70)
    print("Dataset Summary")
    print("=" * 70)



    for name,df in datasets.items():


        print(
            f"{name}: {df.shape}"
        )



# ==========================================================
# Main
# ==========================================================


if __name__ == "__main__":


    datasets = load_all_excel_files()


    show_summary(datasets)


    load_to_database(datasets)