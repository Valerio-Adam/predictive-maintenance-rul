import os
import pandas as pd
from sqlalchemy import create_engine

# =====================================================================
# Database Connection Configuration
# Retrieves settings from environment variables with fallback defaults
# =====================================================================
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "adminpassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "predictive_maintenance")

# Construct PostgreSQL connection URL string for SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Path to the raw input CSV dataset
CSV_PATH = "data/raw/ai4i2020.csv"


def run_ingestion():
    """Reads raw telemetry CSV, formats columns, and loads chronological

    manufacturing cycles into PostgreSQL 'process_telemetry' table.
    """
    print("Connecting to PostgreSQL database...")
    engine = create_engine(DATABASE_URL)

    print(f"Reading raw dataset from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)

    # ------------------------------------------------------------------
    # Data Transformation & Schema Mapping
    # Maps CSV column headers to PostgreSQL table column names
    # ------------------------------------------------------------------
    column_mapping = {
        "UDI": "udi",
        "Product ID": "product_id",
        "Type": "product_type",
        "Air temperature [K]": "air_temp_k",
        "Process temperature [K]": "process_temp_k",
        "Rotational speed [rpm]": "rotational_speed_rpm",
        "Torque [Nm]": "torque_nm",
        "Tool wear [min]": "tool_wear_min",
        "Machine failure": "machine_failure",
        "TWF": "twf",
        "HDF": "hdf",
        "PWF": "pwf",
        "OSF": "osf",
        "RNF": "rnf",
    }

    # Rename columns to match database schema
    df_clean = df.rename(columns=column_mapping)

    # Ensure explicit integer/float types for schema consistency
    df_clean["udi"] = df_clean["udi"].astype(int)
    df_clean["rotational_speed_rpm"] = df_clean["rotational_speed_rpm"].astype(int)
    df_clean["tool_wear_min"] = df_clean["tool_wear_min"].astype(int)
    df_clean["machine_failure"] = df_clean["machine_failure"].astype(int)
    df_clean["twf"] = df_clean["twf"].astype(int)
    df_clean["hdf"] = df_clean["hdf"].astype(int)
    df_clean["pwf"] = df_clean["pwf"].astype(int)
    df_clean["osf"] = df_clean["osf"].astype(int)
    df_clean["rnf"] = df_clean["rnf"].astype(int)

    # Maintain strict chronological sequence ordered by UDI (1 to 10000)
    df_clean = df_clean.sort_values(by="udi")

    # ------------------------------------------------------------------
    # Data Ingestion execution
    # Load batch dataset directly into 'process_telemetry' table
    # ------------------------------------------------------------------
    print(
        f"Inserting {len(df_clean)} sequential telemetry records into 'process_telemetry'..."
    )
    with engine.begin() as conn:
        df_clean.to_sql(
            "process_telemetry",
            conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

    print(
        "\nData ingestion completed successfully! All 10,000 cycles loaded into PostgreSQL."
    )


if __name__ == "__main__":
    run_ingestion()