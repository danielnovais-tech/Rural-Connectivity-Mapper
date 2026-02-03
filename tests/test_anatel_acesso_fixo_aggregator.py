import csv
from pathlib import Path

import pandas as pd

from data_pipeline.anatel.acesso_fixo_aggregator import (
    aggregate_acesso_fixo,
    discover_acesso_fixo_parquets,
    load_acesso_fixo,
    write_acesso_fixo_outputs,
)
from data_pipeline.connectors.anatel_static_connector import ANATELStaticConnector


def test_acesso_fixo_aggregate_from_parquet(tmp_path: Path) -> None:
    parquet_dir = tmp_path / "bronze" / "anatel"
    parquet_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        [
            {
                "municipio": "Brasilia",
                "uf": "DF",
                "quantidade": 10,
                "velocidade": "34 Mbps a 100 Mbps",
                "tecnologia": "FTTH",
            },
            {
                "municipio": "Brasilia",
                "uf": "DF",
                "quantidade": 5,
                "velocidade": "34 Mbps a 100 Mbps",
                "tecnologia": "DSL",
            },
            {
                "municipio": "Goiania",
                "uf": "GO",
                "quantidade": 2,
                "velocidade": "Até 2 Mbps",
                "tecnologia": "DSL",
            },
        ]
    )
    out_path = parquet_dir / "anatel_acesso_fixo_20260101_000000_deadbeef.parquet"
    df.to_parquet(out_path, index=False)

    files = discover_acesso_fixo_parquets(parquet_dir)
    assert files == [out_path]

    loaded = load_acesso_fixo(files)
    result = aggregate_acesso_fixo(loaded, group_by_technology=True)

    summary = result.summary_by_municipio
    assert {(r.uf, r.municipio): r.total_acessos for r in summary.itertuples(index=False)} == {
        ("DF", "Brasilia"): 15,
        ("GO", "Goiania"): 2,
    }

    by_vel = result.by_velocidade
    assert (
        by_vel[(by_vel.uf == "DF") & (by_vel.municipio == "Brasilia") & (by_vel.velocidade == "34 Mbps a 100 Mbps")][
            "total_acessos"
        ].iloc[0]
        == 15
    )

    by_tec_vel = result.by_tecnologia_velocidade
    assert by_tec_vel is not None
    assert (
        by_tec_vel[(by_tec_vel.uf == "DF") & (by_tec_vel.municipio == "Brasilia") & (by_tec_vel.tecnologia == "FTTH")][
            "total_acessos"
        ].iloc[0]
        == 10
    )

    output_dir = tmp_path / "gold" / "anatel_acesso_fixo"
    written = write_acesso_fixo_outputs(result, output_dir=output_dir)
    assert "municipio_parquet" in written
    assert "municipio_csv" in written
    assert "velocidade_parquet" in written
    assert "report_json" in written


def test_acesso_fixo_connector_to_aggregator(tmp_path: Path) -> None:
    manual_dir = tmp_path / "manual"
    output_dir = tmp_path / "bronze" / "anatel"

    csv_path = manual_dir / "acesso_fixo_sample.csv"
    rows = [
        {
            "municipio": "Brasilia",
            "uf": "DF",
            "quantidade": "10",
            "velocidade": "34 Mbps a 100 Mbps",
            "tecnologia": "FTTH",
        },
        {
            "municipio": "Brasilia",
            "uf": "DF",
            "quantidade": "5",
            "velocidade": "34 Mbps a 100 Mbps",
            "tecnologia": "DSL",
        },
    ]

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    connector = ANATELStaticConnector(manual_dir=manual_dir, output_dir=output_dir)
    results = connector.run()
    assert results and all(r.get("status") == "success" for r in results)

    files = discover_acesso_fixo_parquets(output_dir)
    assert len(files) == 1

    loaded = load_acesso_fixo(files)
    result = aggregate_acesso_fixo(loaded, group_by_technology=False)

    summary = result.summary_by_municipio
    assert len(summary) == 1
    assert int(summary["total_acessos"].iloc[0]) == 15
