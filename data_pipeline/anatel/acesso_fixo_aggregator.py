from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ACESSO_FIXO_GLOB = "anatel_acesso_fixo_*.parquet"


@dataclass(frozen=True)
class AcessoFixoAggregateResult:
    summary_by_municipio: pd.DataFrame
    by_velocidade: pd.DataFrame
    by_tecnologia_velocidade: pd.DataFrame | None
    report: dict[str, Any]


def discover_acesso_fixo_parquets(parquet_dir: Path) -> list[Path]:
    parquet_dir = Path(parquet_dir)
    return sorted(parquet_dir.glob(ACESSO_FIXO_GLOB))


def _normalize_column_name(name: str) -> str:
    text = str(name).strip().lower()
    # Keep it minimal; connector already uses plain ASCII column names.
    return text


def normalize_acesso_fixo_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping: dict[str, str] = {}
    for col in df.columns:
        mapping[col] = _normalize_column_name(col)

    df2 = df.rename(columns=mapping)

    # Known aliases (defensive)
    alias_map = {
        "município": "municipio",
        "cidade": "municipio",
        "estado": "uf",
        "qtde": "quantidade",
    }
    for old, new in alias_map.items():
        if old in df2.columns and new not in df2.columns:
            df2 = df2.rename(columns={old: new})

    return df2


def load_acesso_fixo(parquet_files: list[Path]) -> pd.DataFrame:
    if not parquet_files:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []
    for path in parquet_files:
        df = pd.read_parquet(path)
        df = normalize_acesso_fixo_columns(df)
        df["_source_file"] = path.name
        frames.append(df)

    return pd.concat(frames, ignore_index=True, copy=False)


def aggregate_acesso_fixo(
    df: pd.DataFrame,
    *,
    group_by_technology: bool = False,
    strict: bool = False,
) -> AcessoFixoAggregateResult:
    started_at = datetime.now(timezone.utc)

    if df.empty:
        report = {
            "started_at": started_at.isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "input_rows": 0,
            "output_rows_summary": 0,
            "output_rows_by_velocidade": 0,
            "output_rows_by_tecnologia_velocidade": 0,
            "warnings": ["No input rows"],
        }
        return AcessoFixoAggregateResult(
            summary_by_municipio=pd.DataFrame(),
            by_velocidade=pd.DataFrame(),
            by_tecnologia_velocidade=pd.DataFrame() if group_by_technology else None,
            report=report,
        )

    required = {"municipio", "uf", "quantidade", "velocidade"}
    missing = sorted(required - set(df.columns))
    if missing:
        message = f"Missing required columns: {missing}"
        if strict:
            raise ValueError(message)
        warnings = [message]
    else:
        warnings = []

    df2 = df.copy()

    # Coerce + clean
    for key in ("municipio", "uf", "velocidade", "tecnologia"):
        if key in df2.columns:
            df2[key] = df2[key].astype(str).str.strip()
            df2.loc[df2[key].str.lower().isin({"nan", "none", ""}), key] = pd.NA

    if "quantidade" in df2.columns:
        df2["quantidade"] = pd.to_numeric(df2["quantidade"], errors="coerce").fillna(0)

    # Drop unusable rows
    base_keys = [k for k in ["uf", "municipio", "velocidade"] if k in df2.columns]
    if base_keys:
        before = len(df2)
        df2 = df2.dropna(subset=base_keys)
        dropped = before - len(df2)
        if dropped:
            warnings.append(f"Dropped {dropped} row(s) missing {base_keys}")

    # Summary by municipio
    if {"uf", "municipio", "quantidade"}.issubset(df2.columns):
        summary = (
            df2.groupby(["uf", "municipio"], as_index=False)
            .agg(total_acessos=("quantidade", "sum"), linhas=("quantidade", "size"))
            .sort_values(["uf", "municipio"], kind="stable")
        )
    else:
        summary = pd.DataFrame()

    # Breakdown by velocidade category
    if {"uf", "municipio", "velocidade", "quantidade"}.issubset(df2.columns):
        by_vel = (
            df2.groupby(["uf", "municipio", "velocidade"], as_index=False)
            .agg(total_acessos=("quantidade", "sum"), linhas=("quantidade", "size"))
            .sort_values(["uf", "municipio", "velocidade"], kind="stable")
        )
    else:
        by_vel = pd.DataFrame()

    by_tec_vel: pd.DataFrame | None
    if group_by_technology and {"uf", "municipio", "tecnologia", "velocidade", "quantidade"}.issubset(df2.columns):
        by_tec_vel = (
            df2.groupby(["uf", "municipio", "tecnologia", "velocidade"], as_index=False)
            .agg(total_acessos=("quantidade", "sum"), linhas=("quantidade", "size"))
            .sort_values(["uf", "municipio", "tecnologia", "velocidade"], kind="stable")
        )
    elif group_by_technology:
        by_tec_vel = pd.DataFrame()
    else:
        by_tec_vel = None

    ended_at = datetime.now(timezone.utc)
    report = {
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "input_rows": int(len(df2)),
        "output_rows_summary": int(len(summary)),
        "output_rows_by_velocidade": int(len(by_vel)),
        "output_rows_by_tecnologia_velocidade": int(len(by_tec_vel)) if by_tec_vel is not None else 0,
        "columns_seen": sorted(df.columns.astype(str).tolist()),
        "warnings": warnings,
    }

    # Include connector metadata stats if present
    if "_processamento_data" in df.columns:
        report["processamento_data_min"] = str(df["_processamento_data"].min())
        report["processamento_data_max"] = str(df["_processamento_data"].max())

    return AcessoFixoAggregateResult(
        summary_by_municipio=summary,
        by_velocidade=by_vel,
        by_tecnologia_velocidade=by_tec_vel,
        report=report,
    )


def write_acesso_fixo_outputs(
    result: AcessoFixoAggregateResult,
    *,
    output_dir: Path,
    prefix: str = "acesso_fixo",
) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    written: dict[str, str] = {}

    def _write_df(name: str, df: pd.DataFrame) -> None:
        parquet_path = output_dir / f"{prefix}_{name}_{ts}.parquet"
        csv_path = output_dir / f"{prefix}_{name}_{ts}.csv"

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False, encoding="utf-8")

        written[f"{name}_parquet"] = str(parquet_path)
        written[f"{name}_csv"] = str(csv_path)

    if not result.summary_by_municipio.empty:
        _write_df("municipio", result.summary_by_municipio)

    if not result.by_velocidade.empty:
        _write_df("velocidade", result.by_velocidade)

    if result.by_tecnologia_velocidade is not None and not result.by_tecnologia_velocidade.empty:
        _write_df("tecnologia_velocidade", result.by_tecnologia_velocidade)

    report_path = output_dir / f"{prefix}_report_{ts}.json"
    report_payload = dict(result.report)
    report_payload["outputs"] = written

    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    written["report_json"] = str(report_path)

    return written
