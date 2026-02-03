import argparse
from pathlib import Path

from data_pipeline.anatel.acesso_fixo_aggregator import (
    aggregate_acesso_fixo,
    discover_acesso_fixo_parquets,
    load_acesso_fixo,
    write_acesso_fixo_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate ANATEL acesso_fixo datasets (no coordinates) by UF/municipio."
    )
    parser.add_argument(
        "--anatel-parquet-dir",
        default=str(Path("data") / "bronze" / "anatel"),
        help="Directory containing anatel_acesso_fixo_*.parquet files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path("data") / "gold" / "anatel_acesso_fixo"),
        help="Directory to write aggregated outputs.",
    )
    parser.add_argument(
        "--group-by-technology",
        action="store_true",
        help="Also generate breakdown by tecnologia + velocidade.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if required columns are missing.",
    )

    args = parser.parse_args()

    parquet_dir = Path(args.anatel_parquet_dir)
    output_dir = Path(args.output_dir)

    parquet_files = discover_acesso_fixo_parquets(parquet_dir)
    df = load_acesso_fixo(parquet_files)

    result = aggregate_acesso_fixo(
        df,
        group_by_technology=args.group_by_technology,
        strict=args.strict,
    )
    written = write_acesso_fixo_outputs(result, output_dir=output_dir)

    print("✅ acesso_fixo aggregation complete")
    print(f"  Input files: {len(parquet_files)}")
    print(f"  Output dir:  {output_dir}")
    for key, value in written.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
