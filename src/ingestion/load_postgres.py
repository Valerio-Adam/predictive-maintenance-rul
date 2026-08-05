import os
import pandas as pd
from sqlalchemy import create_engine

# Configuration: Retrieve database connection settings from environment variables
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "adminpassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "predictive_maintenance")

# Construct the PostgreSQL connection URL string for SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Path to the raw input CSV file
CSV_PATH = "data/raw/ai4i2020.csv"


def run_ingestion():
    """Main execution function to load CSV data into the PostgreSQL database."""
    print("Connecting to PostgreSQL database...")
    # Initialize the SQLAlchemy database engine using the connection URL
    engine = create_engine(DATABASE_URL)

    print(f"Reading dataset from {CSV_PATH}...")
    # Read the raw CSV dataset into a pandas DataFrame
    df = pd.read_csv(CSV_PATH)

    # --------------------------------------------------------------------------
    # Step 1: Extract and populate the 'machines' table
    # --------------------------------------------------------------------------
    # Select machine metadata columns and remove duplicate entries
    machines_df = df[["Product ID", "Type"]].drop_duplicates()

    # Rename DataFrame columns to match PostgreSQL table schema names
    machines_df = machines_df.rename(
        columns={"Product ID": "product_id", "Type": "product_type"}
    )

    # Open a database connection block and insert machine records into 'machines'
    with engine.begin() as conn:
        machines_df.to_sql(
            "machines", conn, if_exists="append", index=False, method="multi"
        )
    print(f"Successfully loaded {len(machines_df)} rows into 'machines'.")

    # --------------------------------------------------------------------------
    # Step 2: Extract failure events and populate 'maintenance_events' table
    # --------------------------------------------------------------------------
    # List of binary failure indicator columns present in the CSV
    failure_cols = ["TWF", "HDF", "PWF", "OSF", "RNF"]
    failure_events = []

    # Filter rows where a machine failure occurred (Machine failure == 1)
    failed_rows = df[df["Machine failure"] == 1]

    # Iterate over failed rows to unpivot failure flags into individual records
    for index, row in failed_rows.iterrows():
        for code in failure_cols:
            # Check if a specific failure type is flagged positive (1)
            if row[code] == 1:
                failure_events.append(
                    {
                        "product_id": row["Product ID"],
                        "failure_code": code,
                        "air_temp_k": row["Air temperature [K]"],
                        "process_temp_k": row["Process temperature [K]"],
                        "rotational_speed_rpm": row["Rotational speed [rpm]"],
                        "torque_nm": row["Torque [Nm]"],
                        "tool_wear_min": row["Tool wear [min]"],
                    }
                )

    # Convert the list of failure dictionaries into a structured DataFrame
    events_df = pd.DataFrame(failure_events)

    # Open a database connection block and insert records into 'maintenance_events'
    with engine.begin() as conn:
        events_df.to_sql(
            "maintenance_events", conn, if_exists="append", index=False
        )
    print(
        f"Successfully loaded {len(events_df)} failure records into 'maintenance_events'."
    )

    print("\nData ingestion pipeline completed successfully!")


# Execute the script if run directly from the terminal
if __name__ == "__main__":
    run_ingestion()