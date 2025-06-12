import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(
        description="Combine one or more Parquet files into a single Parquet."
    )
    parser.add_argument(
        "inputs", nargs="+", help="Input Parquet file paths to concatenate"
    )
    parser.add_argument(
        "-o", "--output",
        default="combined.parquet",
        help="Output Parquet file path (default: combined.parquet)"
    )
    args = parser.parse_args()

    # Read all inputs into DataFrames
    dfs = [pd.read_parquet(p) for p in args.inputs]

    # Concatenate (headers preserved only once)
    combined = pd.concat(dfs, ignore_index=True)

    # Write out
    combined.to_parquet(args.output)
    print(f"✅ Combined {len(args.inputs)} files → {args.output}")

    counts = combined["location"].value_counts()
    print("📊 Counts per location:")
    for loc, cnt in counts.items():
        print(f"  - {loc}: {cnt}")

if __name__ == "__main__":
    main()