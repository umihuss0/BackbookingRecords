# Backbooking Records Analyzer

Version: v0.2.0

Analyze RTB revenue data and generate copy-ready, monospaced reports for PMP/OE totals, advertisers, and weekly rollups. Built with Streamlit for fast, zero‑ops deployment.

## Features

- File upload: CSV/XLS/XLSX with expected columns:
  - Date - EST, RTB Channel, RTB Advertiser, RTB SSP, System, RTB Deal ID, RTB Creative ID, Revenue
- Data cleaning:
  - Fuzzy column matching (minor header variations map correctly)
  - Date parsing; revenue normalized from currency strings
- Formatted tabs (primary views; leftmost):
  - Formatted: Totals (PMP/OE)
  - Formatted: Advertiser (PMP/OE) — shows top N advertisers per section; header includes total account counts
  - Formatted: Advertiser by Week — 4‑week buckets per month (W1–W4); blocks by OE then PMP
- Non-formatted analytics:
  - Revenue by Date
  - By RTB Channel
  - By RTB Advertiser (includes top RTB SSP per advertiser)
  - By RTB SSP
  - By System
- Currency formatting:
  - ≥ $1 shows no cents (rounded); < $1 shows cents (e.g., $0.26)
- Copy-friendly formatting rules:
  - Monospaced, ASCII rows; right-aligned amounts at a fixed column (default 40)
  - Width ≤ 80 chars; long advertiser names truncated with ellipsis
  - Unicode mathematical bold used only in header lines (A–Z, a–z, 0–9)

## Run Locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy on Streamlit Cloud

- Repo: this repository
- Branch: main
- Main file path: `streamlit_app.py`
- Python: pinned via `runtime.txt` → `python-3.11`
- Deps: `requirements.txt` (streamlit, pandas, openpyxl)

## Usage Notes

- Upload a CSV/XLSX with the required columns (order not required).
- Use the left sidebar to set date range and “Top N” rows.
- Copy from the “Formatted” tabs for paste‑ready text blocks. These enforce:
  - Right-aligned currency with spaces
  - Page width ≤ 80
  - Unicode bold headers only; table rows are plain ASCII

## Changelog

v0.2.0
- Added Streamlit app (`streamlit_app.py`) and processing engine (`processing.py`).
- Formatted tabs for Totals, Advertiser, and Weekly views with copy‑ready output.
- Weekly view uses 4‑week buckets per month (W1–W4).
- Currency display rule: cents only for values < $1.
- “By RTB Advertiser” table now includes top RTB SSP column.
- Tabs reordered to prioritize formatted views.

v0.1.0
- Initial frontend scaffolding (Vite + React + shadcn + Tailwind).
