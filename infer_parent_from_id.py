import pandas as pd
import argparse

"""
Given an input csv file. Load the csv file and add a new column 'parent' based on the 'LABEL' column.
The 'parent' column should calculated by removing last character from the 'LABEL' column, and removing
the trailing '.' if it is there.
"""

REFERENCE_TABLE = "./in/totally_final_version.csv"
df = pd.read_csv(REFERENCE_TABLE)


def infer_parent_from_id(input_csv, output_csv):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(input_csv)

    # Add a new column 'parent' based on the 'LABEL' column
    def calculate_parent(label):
        if isinstance(label, str):
            if "." not in label:
                return label
            parent = label[:-1].rstrip(".")
            # check if parent exists in the LABEL column
            if parent not in df["LABEL"].values:
                # If parent does not exist, return the original label
                return label
        return parent

    df["parent"] = df["LABEL"].apply(calculate_parent)
    # Reorder columns so 'parent' is the second column
    cols = list(df.columns)
    cols.insert(1, cols.pop(cols.index("parent")))
    df = df[cols]

    # Save the updated DataFrame to a new CSV file
    df.to_csv(output_csv, index=False)


# Example usage
# infer_parent_from_id('input.csv', 'output.csv')

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Infer parent from LABEL column in a CSV file."
    )
    parser.add_argument("input_csv", help="Path to the input CSV file")
    parser.add_argument("output_csv", help="Path to the output CSV file")

    # Parse the arguments
    args = parser.parse_args()

    # Call the function with the provided arguments
    infer_parent_from_id(args.input_csv, args.output_csv)
