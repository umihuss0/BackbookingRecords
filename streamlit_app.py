import io
import subprocess
from datetime import date
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

from processing import (
    REQUIRED_COLUMNS,
    compute_sections,
    df_to_markdown,
    df_to_tsv,
    read_and_normalize,
    total_by_channel,
    pairs_advertiser_by_channel,
    advertiser_by_week_pairs,
    build_two_section_report,
)


st.set_page_config(page_title="Backbooking Records Analyzer", layout="wide")

APP_VERSION = "v0.2.1"

def _git_sha_short() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return ""


def _show_copy_block(label: str, text: str) -> None:
    """Render a copy-friendly text area plus download button for quick reuse."""
    with st.expander(f"Copy/Paste: {label}", expanded=False):
        st.text_area("", text, height=200)
        st.download_button(
            label=f"Download {label} (.tsv)",
            data=text.encode("utf-8"),
            file_name=f"{label.lower().replace(' ', '_')}.tsv",
            mime="text/tab-separated-values",
            use_container_width=True,
        )


def main() -> None:
    st.title("Backbooking Records Analyzer")
    sha = _git_sha_short()
    version_line = f"{APP_VERSION}" + (f" • {sha}" if sha else "")
    st.caption(
        "Upload your CSV/Excel with the expected columns to get instant summaries. "
        + version_line
    )

    with st.sidebar:
        st.header("Upload & Filters")
        uploaded = st.file_uploader(
            "Upload a CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=False,
            help="The file should contain: "
            + ", ".join(REQUIRED_COLUMNS),
        )
        top_n = st.number_input("Top N rows per section", min_value=5, max_value=1000, value=25, step=5)
        show_markdown = st.checkbox("Show Markdown tables instead of TSV", value=False)

    if not uploaded:
        st.info(
            "Upload a file to begin. Expected columns: " + ", ".join(REQUIRED_COLUMNS)
        )
        return

    try:
        df = read_and_normalize(uploaded)
    except Exception as e:
        st.error(f"Could not read the file: {e}")
        return

    # Filters
    min_dt = pd.to_datetime(df["Date - EST"]).min().date() if not df.empty else date.today()
    max_dt = pd.to_datetime(df["Date - EST"]).max().date() if not df.empty else date.today()
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        start_date = st.date_input("Start date", value=min_dt, min_value=min_dt, max_value=max_dt)
    with c2:
        end_date = st.date_input("End date", value=max_dt, min_value=min_dt, max_value=max_dt)
    with c3:
        st.write("")
        st.write("")
        st.success(
            f"Loaded {len(df):,} rows from {uploaded.name}. Date range: {min_dt} → {max_dt}"
        )

    # Apply date filter
    m = (pd.to_datetime(df["Date - EST"]).dt.date >= start_date) & (
        pd.to_datetime(df["Date - EST"]).dt.date <= end_date
    )
    df_f = df.loc[m].copy()

    # Top-level KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Revenue", f"${df_f['Revenue'].sum():,.2f}")
    with k2:
        st.metric("Advertisers", df_f["RTB Advertiser"].nunique())
    with k3:
        st.metric("Deals", df_f["RTB Deal ID"].nunique())
    with k4:
        st.metric("Creatives", df_f["RTB Creative ID"].nunique())

    sections = compute_sections(df_f, top_n=top_n)

    tab_labels = list(sections.keys())
    tabs = st.tabs(tab_labels + [
        "Formatted: Totals (PMP/OE)",
        "Formatted: Advertiser (PMP/OE)",
        "Formatted: Advertiser by Week",
    ])
    for tab, label in zip(tabs, tab_labels):
        with tab:
            gdf = sections[label]
            st.caption(f"Rows: {len(gdf)}")
            st.dataframe(
                gdf,
                use_container_width=True,
                hide_index=True,
            )

            # Copy-ready text
            if show_markdown:
                text_export = df_to_markdown(gdf)
                _show_copy_block(f"{label} (Markdown)", text_export)
            else:
                text_export = df_to_tsv(gdf)
                _show_copy_block(f"{label} (TSV)", text_export)

    # Add formatted views
    # Totals view
    with tabs[-3]:
        st.subheader("PMP / OE Breakout Total")
        amount_col = st.number_input("Amount column stop (38–44)", min_value=30, max_value=60, value=40)
        page_width = st.number_input("Page width (<= 80)", min_value=42, max_value=80, value=80)

        total_pmp = total_by_channel(df_f, "PMP")
        total_oe = total_by_channel(df_f, "OE")
        # Empty pairs; headers show totals
        report = build_two_section_report(
            "OE", [], total_oe,
            "PMP", [], total_pmp,
            amount_col=amount_col,
            page_width=page_width,
            section_rule=False,
            separator_rule=True,
        )
        st.code(report)

    # Advertiser breakout
    with tabs[-2]:
        st.subheader("PMP / OE Breakout by Advertiser")
        amount_col2 = st.number_input("Amount column stop (38–44) ", min_value=30, max_value=60, value=40, key="amt2")
        page_width2 = st.number_input("Page width (<= 80)  ", min_value=42, max_value=80, value=80, key="pw2")
        top_n_adv = st.number_input("Top advertisers per section", min_value=5, max_value=1000, value=50, step=5)

        pairs_oe = pairs_advertiser_by_channel(df_f, "OE")[: top_n_adv]
        pairs_pmp = pairs_advertiser_by_channel(df_f, "PMP")[: top_n_adv]
        total_pmp = sum(v for _, v in pairs_pmp)
        total_oe = sum(v for _, v in pairs_oe)

        report = build_two_section_report(
            "OE", pairs_oe, total_oe,
            "PMP", pairs_pmp, total_pmp,
            amount_col=amount_col2,
            page_width=page_width2,
            section_rule=False,
            separator_rule=True,
        )
        st.code(report)

    # Advertiser by week
    with tabs[-1]:
        st.subheader("PMP / OE Breakout by Advertiser by Week")
        amount_col3 = st.number_input("Amount column stop (38–44)", min_value=30, max_value=60, value=40, key="amt3")
        page_width3 = st.number_input("Page width (<= 80)", min_value=42, max_value=80, value=80, key="pw3")
        top_n_w = st.number_input("Top advertisers per week", min_value=5, max_value=1000, value=25, step=5)

        wk_pairs_oe = advertiser_by_week_pairs(df_f, "OE")
        wk_pairs_pmp = advertiser_by_week_pairs(df_f, "PMP")
        all_weeks = sorted(set(wk_pairs_oe.keys()) | set(wk_pairs_pmp.keys()), key=lambda x: int(x.split()[-1]))

        for wk in all_weeks:
            st.caption(wk)
            pairs_oe = (wk_pairs_oe.get(wk) or [])[: top_n_w]
            pairs_pmp = (wk_pairs_pmp.get(wk) or [])[: top_n_w]
            total_oe = sum(v for _, v in pairs_oe)
            total_pmp = sum(v for _, v in pairs_pmp)
            report = build_two_section_report(
                "OE", pairs_oe, total_oe,
                "PMP", pairs_pmp, total_pmp,
                amount_col=amount_col3,
                page_width=page_width3,
                section_rule=False,
                separator_rule=True,
            )
            st.code(report)


if __name__ == "__main__":
    main()
