from __future__ import annotations

import io
import re
from typing import Dict, Iterable, List, Mapping, Tuple
import math

import pandas as pd


# Expected columns in the uploaded file (order not required)
REQUIRED_COLUMNS: List[str] = [
    "Date - EST",
    "RTB Channel",
    "RTB Advertiser",
    "RTB SSP",
    "System",
    "RTB Deal ID",
    "RTB Creative ID",
    "Revenue",
]


def _canonicalize(col: str) -> str:
    """Normalize a column name for fuzzy matching.

    Lowercases, trims, and removes extra punctuation/whitespace differences.
    """
    if col is None:
        return ""
    s = str(col).strip().lower()
    # Replace all non-alphanum with a single space, then squeeze
    s = re.sub(r"[^0-9a-z]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _build_column_map(cols: Iterable[str]) -> Dict[str, str]:
    """Map fuzzy-normalized input columns to the required canonical column names."""
    # Build lookup for incoming columns
    incoming = {_canonicalize(c): c for c in cols}

    candidates: Dict[str, List[str]] = {
        "Date - EST": ["date est", "date"],
        "RTB Channel": ["rtb channel", "channel"],
        "RTB Advertiser": ["rtb advertiser", "advertiser"],
        "RTB SSP": ["rtb ssp", "ssp"],
        "System": ["system"],
        "RTB Deal ID": ["rtb deal id", "deal id", "deal"],
        "RTB Creative ID": ["rtb creative id", "creative id", "creative"],
        "Revenue": ["revenue", "rev", "amount"],
    }

    mapping: Dict[str, str] = {}
    for canonical, keys in candidates.items():
        for key in keys:
            if key in incoming:
                mapping[canonical] = incoming[key]
                break
    return mapping


def read_and_normalize(uploaded) -> pd.DataFrame:
    """Read an uploaded CSV/Excel stream and normalize columns and types."""
    name = (uploaded.name or "").lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded)
    else:
        # Try UTF-8 then fallback to latin-1
        try:
            df = pd.read_csv(uploaded)
        except UnicodeDecodeError:
            uploaded.seek(0)
            df = pd.read_csv(uploaded, encoding="latin-1")

    if df.empty:
        return df

    # Normalize whitespace in headers
    df.columns = [str(c).strip() for c in df.columns]

    # Fuzzy map incoming columns to required names
    mapping = _build_column_map(df.columns)
    missing = [c for c in REQUIRED_COLUMNS if c not in mapping]
    if missing:
        # If some canonical are already present exactly, include them
        still_missing = [
            c for c in missing if c not in df.columns
        ]
        if still_missing:
            raise ValueError(
                "Missing required columns: " + ", ".join(still_missing)
            )

    # Prepare a view with canonical names
    for canonical in REQUIRED_COLUMNS:
        if canonical in df.columns:
            # Already present
            continue
        if canonical in mapping:
            df.rename(columns={mapping[canonical]: canonical}, inplace=True)

    # Coerce types
    # Dates
    if "Date - EST" in df.columns:
        df["Date - EST"] = pd.to_datetime(df["Date - EST"], errors="coerce")

    # Revenue: strip currency/commas and coerce numeric
    if "Revenue" in df.columns:
        df["Revenue"] = (
            df["Revenue"].astype(str).str.replace(r"[^0-9.\-]", "", regex=True)
        )
        df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce").fillna(0.0)

    # Trim whitespace in key string columns
    for c in [
        "RTB Channel",
        "RTB Advertiser",
        "RTB SSP",
        "System",
        "RTB Deal ID",
        "RTB Creative ID",
    ]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    return df


def _group_sum(df: pd.DataFrame, by: List[str]) -> pd.DataFrame:
    g = (
        df.groupby(by, dropna=False, as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
    )
    # Round for display
    g["Revenue"] = g["Revenue"].round(2)
    return g


def compute_sections(df: pd.DataFrame, top_n: int = 25) -> Dict[str, pd.DataFrame]:
    """Build a set of ready-to-display sections."""
    out: Dict[str, pd.DataFrame] = {}
    if df.empty:
        return out

    # Daily revenue
    daily = df.copy()
    daily["Date"] = pd.to_datetime(daily["Date - EST"]).dt.date
    out["Revenue by Date"] = _group_sum(daily, ["Date"]).head(top_n)

    # Single-dimension summaries
    # By RTB Channel
    out["By RTB Channel"] = _group_sum(df, ["RTB Channel"]).head(top_n)

    # By RTB Advertiser with accompanying top RTB SSP
    adv_totals = _group_sum(df, ["RTB Advertiser"]).head(10_000)
    ssp_g = (
        df.groupby(["RTB Advertiser", "RTB SSP"], dropna=False)["Revenue"].sum()
        .reset_index()
        .sort_values(["RTB Advertiser", "Revenue"], ascending=[True, False])
    )
    top_ssp = ssp_g.drop_duplicates(subset=["RTB Advertiser"], keep="first")[["RTB Advertiser", "RTB SSP"]]
    adv_merged = adv_totals.merge(top_ssp, on="RTB Advertiser", how="left")
    adv_merged = adv_merged[[c for c in ["RTB Advertiser", "RTB SSP", "Revenue"] if c in adv_merged.columns]]
    out["By RTB Advertiser"] = adv_merged.head(top_n)

    # Other single dimensions
    out["By RTB SSP"] = _group_sum(df, ["RTB SSP"]).head(top_n)
    out["By System"] = _group_sum(df, ["System"]).head(top_n)

    # Context-rich summaries
    out["By Deal ID"] = _group_sum(df, ["RTB Deal ID", "RTB Advertiser"]).head(top_n)
    out["By Creative ID"] = _group_sum(df, ["RTB Creative ID", "RTB Advertiser"]).head(top_n)

    return out


def df_to_tsv(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    # Header
    buf.write("\t".join(map(str, df.columns.tolist())))
    buf.write("\n")
    for _, row in df.iterrows():
        vals = ["" if pd.isna(v) else str(v) for v in row.tolist()]
        buf.write("\t".join(vals))
        buf.write("\n")
    return buf.getvalue()


def df_to_markdown(df: pd.DataFrame) -> str:
    # Simple markdown generator without external deps
    cols = [str(c) for c in df.columns.tolist()]
    header = "| " + " | ".join(_escape_md(str(c)) for c in cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [header, sep]
    for _, row in df.iterrows():
        vals = ["" if pd.isna(v) else str(v) for v in row.tolist()]
        lines.append("| " + " | ".join(_escape_md(v) for v in vals) + " |")
    return "\n".join(lines)


def _escape_md(s: str) -> str:
    # Escape pipes used in markdown tables
    return s.replace("|", "\\|")


# ---------------------- Custom PMP/OE views ----------------------


def classify_channel(value: str) -> str | None:
    """Map RTB Channel strings to 'PMP' or 'OE' buckets.

    Returns 'PMP', 'OE', or None when unclassified.
    """
    if value is None:
        return None
    v = str(value).strip().lower()
    if not v:
        return None
    # PMP-like tokens
    if any(t in v for t in ["pmp", "private", "preferred", "deal", "programmatic guaranteed", "pg"]):
        return "PMP"
    # OE-like tokens
    if any(t in v for t in ["oe", "open exchange", "open", "open auction"]):
        return "OE"
    return None


def ensure_channel_bucket(df: pd.DataFrame) -> pd.DataFrame:
    if "_ChannelBucket" in df.columns:
        return df
    out = df.copy()
    out["_ChannelBucket"] = out["RTB Channel"].apply(classify_channel)
    return out


def format_usd(amount: float) -> str:
    """US currency with rule: show cents only if abs(value) < 1."""
    a = float(amount)
    sign = "-" if a < 0 else ""
    a_abs = abs(a)
    if a_abs == 0:
        core = "0"
    elif a_abs < 1:
        core = f"{a_abs:,.2f}"
    else:
        core = f"{int(round(a_abs)):,.0f}"
    return f"{sign}${core}"


def _truncate_left(left: str, max_chars: int) -> str:
    if len(left) <= max_chars:
        return left
    if max_chars <= 3:
        return left[:max_chars]
    return left[: max_chars - 3] + "..."


def format_section_block(
    section: str,
    pairs: List[tuple[str, float]],
    section_total: float,
    *,
    amount_col: int = 40,
    page_width: int = 80,
    max_left_chars: int | None = None,
    include_rule: bool = False,
    header_override: str | None = None,
) -> str:
    """Return a text block for one section with a header and aligned rows.

    pairs must be sorted in display order (descending by amount).
    """
    header = (
        header_override
        if header_override is not None
        else f"{section} ({format_usd(section_total)}) All Accounts (Overall Total)"
    )
    header = _bold_alnum(header)
    width = min(max(42, amount_col + 20), page_width)
    rule = "=" * width
    lines: List[str] = [header]
    if include_rule:
        lines.append(rule)

    # Determine max left length so right part always fits page_width
    max_right = max((len(format_usd(v)) for _, v in pairs), default=len("$0"))
    # Ensure amount_col leaves at least one space between left and right
    effective_amount_col = max(1, min(amount_col, width - max_right - 1))
    if max_left_chars is None:
        # Avoid left text pushing us beyond width
        max_left_chars = min(34, effective_amount_col - 1)

    for left, value in pairs:
        left = _truncate_left(str(left), max_left_chars)
        right = format_usd(float(value))
        spaces = max(1, effective_amount_col - len(left) - len(right))
        line = f"{left}{' ' * spaces}{right}"
        # Final guard: trim if over width (very long right values)
        if len(line) > width:
            line = line[:width]
        lines.append(line)

    return "\n".join(lines)


def build_two_section_report(
    left_name: str,
    left_pairs: List[tuple[str, float]],
    left_total: float,
    right_name: str,
    right_pairs: List[tuple[str, float]],
    right_total: float,
    *,
    amount_col: int = 40,
    page_width: int = 80,
    section_rule: bool = False,
    separator_rule: bool = True,
    header_left: str | None = None,
    header_right: str | None = None,
) -> str:
    block_left = format_section_block(
        left_name,
        left_pairs,
        left_total,
        amount_col=amount_col,
        page_width=page_width,
        include_rule=section_rule,
        header_override=header_left,
    )
    block_right = format_section_block(
        right_name,
        right_pairs,
        right_total,
        amount_col=amount_col,
        page_width=page_width,
        include_rule=section_rule,
        header_override=header_right,
    )
    if separator_rule:
        rule = "=" * min(page_width, max(42, amount_col + 20))
        return f"{block_left}\n{rule}\n{block_right}"
    return f"{block_left}\n\n{block_right}"


def pairs_advertiser_by_channel(df: pd.DataFrame, channel: str) -> List[tuple[str, float]]:
    dfb = ensure_channel_bucket(df)
    mask = dfb["_ChannelBucket"] == channel
    g = (
        dfb.loc[mask]
        .groupby(["RTB Advertiser"], dropna=False)["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    return [(row["RTB Advertiser"], float(row["Revenue"])) for _, row in g.iterrows()]


def total_by_channel(df: pd.DataFrame, channel: str) -> float:
    dfb = ensure_channel_bucket(df)
    return float(dfb.loc[dfb["_ChannelBucket"] == channel, "Revenue"].sum())


def week_index_relative(d: pd.Timestamp, start: pd.Timestamp) -> int:
    return int(((pd.to_datetime(d).normalize() - start.normalize()).days) // 7) + 1


def add_relative_week(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["_Week"] = []
        return df
    out = df.copy()
    start = pd.to_datetime(out["Date - EST"]).min()
    out["_Week"] = pd.to_datetime(out["Date - EST"]).apply(lambda d: f"Week {week_index_relative(d, start)}")
    return out


def advertiser_by_week_pairs(df: pd.DataFrame, channel: str) -> Dict[str, List[tuple[str, float]]]:
    """Return mapping of week label -> list[(advertiser, revenue)]."""
    if df.empty:
        return {}
    dfb = ensure_channel_bucket(df)
    dfw = add_relative_week(dfb)
    mask = dfw["_ChannelBucket"] == channel
    g = (
        dfw.loc[mask]
        .groupby(["_Week", "RTB Advertiser"], dropna=False)["Revenue"]
        .sum()
        .reset_index()
        .sort_values(["_Week", "Revenue"], ascending=[True, False])
    )
    out: Dict[str, List[tuple[str, float]]] = {}
    for wk, sub in g.groupby("_Week", sort=True):
        out[wk] = [(row["RTB Advertiser"], float(row["Revenue"])) for _, row in sub.iterrows()]
    return out


# ---- Four-week-per-month utilities ----


def add_four_week_in_month(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["_MonthKey"], df["_MonthLabel"], df["_W4"] = [], [], []
        return df
    out = df.copy()
    dt = pd.to_datetime(out["Date - EST"], errors="coerce")
    out["_MonthKey"] = dt.dt.strftime("%Y-%m")
    out["_MonthLabel"] = dt.dt.strftime("%b %Y")
    day = dt.dt.day.astype("float")
    dim = dt.dt.days_in_month.astype("float")
    bucket = (((day - 1) * 4) // dim + 1).fillna(1).clip(lower=1, upper=4).astype(int)
    out["_W4"] = "W" + bucket.astype(str)
    return out


def advertiser_by_month_week4_pairs(
    df: pd.DataFrame, channel: str
) -> Tuple[Dict[str, str], Dict[str, Dict[str, List[tuple[str, float]]]]]:
    if df.empty:
        return {}, {}
    dfb = ensure_channel_bucket(df)
    dfw = add_four_week_in_month(dfb)
    mask = dfw["_ChannelBucket"] == channel
    g = (
        dfw.loc[mask]
        .groupby(["_MonthKey", "_MonthLabel", "_W4", "RTB Advertiser"], dropna=False)["Revenue"]
        .sum()
        .reset_index()
        .sort_values(["_MonthKey", "_W4", "Revenue"], ascending=[True, True, False])
    )
    months: Dict[str, str] = {}
    data: Dict[str, Dict[str, List[tuple[str, float]]]] = {}
    for (mkey, mlabel, w4), sub in g.groupby(["_MonthKey", "_MonthLabel", "_W4"], sort=True):
        months[mkey] = mlabel
        pairs = [(row["RTB Advertiser"], float(row["Revenue"])) for _, row in sub.iterrows()]
        data.setdefault(mkey, {})[w4] = pairs
    return months, data


def _bold_alnum(s: str) -> str:
    out_chars: List[str] = []
    for ch in s:
        o = ord(ch)
        if 0x41 <= o <= 0x5A:  # A-Z
            out_chars.append(chr(0x1D400 + (o - 0x41)))
        elif 0x61 <= o <= 0x7A:  # a-z
            out_chars.append(chr(0x1D41A + (o - 0x61)))
        elif 0x30 <= o <= 0x39:  # 0-9
            out_chars.append(chr(0x1D7CE + (o - 0x30)))
        else:
            out_chars.append(ch)
    return "".join(out_chars)
