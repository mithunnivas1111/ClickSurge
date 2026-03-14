"""
GSC CSV Normalizer

Google Search Console exports use different column names and formats
than what the analyzers expect. This normalizer maps them automatically.

GSC Page Export:    Top pages, Clicks, Impressions, CTR, Position
GSC Query Export:   Top queries, Clicks, Impressions, CTR, Position
CTR format:         "4.09%" string → 0.0409 float
"""

import pandas as pd


# Column name mappings — maps any known GSC variant → internal name
PAGE_COL_MAP = {
    'top pages':    'page',
    'page':         'page',
    'url':          'page',
    'landing page': 'page',
    'clicks':       'clicks',
    'impressions':  'impressions',
    'ctr':          'ctr',
    'position':     'position',
    'avg. position':'position',
}

QUERY_COL_MAP = {
    'top queries':  'query',
    'query':        'query',
    'keyword':      'query',
    'search query': 'query',
    'clicks':       'clicks',
    'impressions':  'impressions',
    'ctr':          'ctr',
    'position':     'position',
    'avg. position':'position',
}


def _rename_cols(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    """Rename columns using case-insensitive mapping."""
    rename = {}
    for col in df.columns:
        mapped = col_map.get(col.lower().strip())
        if mapped:
            rename[col] = mapped
    return df.rename(columns=rename)


def _fix_ctr(df: pd.DataFrame) -> pd.DataFrame:
    """Convert CTR from '4.09%' string → 0.0409 float if needed."""
    if 'ctr' not in df.columns:
        return df
    sample = df['ctr'].dropna().head(5)
    # Already float
    if pd.api.types.is_float_dtype(df['ctr']):
        return df
    # String like "4.09%"
    try:
        df['ctr'] = df['ctr'].astype(str).str.replace('%', '', regex=False).str.strip().astype(float) / 100
    except Exception:
        pass
    return df


def _fix_numeric(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Ensure numeric columns are numeric (strip commas etc.)."""
    for col in cols:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(',', '', regex=False).str.strip(),
                    errors='coerce'
                ).fillna(0)
            except Exception:
                pass
    return df


def normalize_page_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a GSC Page Performance CSV export.
    Handles any column naming variant from GSC.
    Returns df with standard columns: page, impressions, clicks, ctr, position
    """
    df = df.copy()
    df = _rename_cols(df, PAGE_COL_MAP)
    df = _fix_ctr(df)
    df = _fix_numeric(df, ['impressions', 'clicks', 'position'])

    required = ['page', 'impressions', 'clicks', 'ctr', 'position']
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Could not find required columns after normalization. Missing: {missing}\n"
            f"Your columns: {list(df.columns)}\n"
            f"Expected one of: 'Top pages' / 'page' / 'url' for the URL column."
        )

    # Drop rows with no page URL
    df = df.dropna(subset=['page'])
    df = df[df['page'].astype(str).str.startswith('http')]

    # Ensure types
    df['impressions'] = df['impressions'].astype(int)
    df['clicks']      = df['clicks'].astype(int)
    df['position']    = df['position'].astype(float)
    df['ctr']         = df['ctr'].astype(float)

    return df.reset_index(drop=True)


def normalize_query_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a GSC Page-Query CSV export.
    Returns df with standard columns: query, impressions, clicks, ctr, position
    For cannibalization we also need 'page' — if only queries are present,
    we return the query-level data as-is (cannibalization requires page+query).
    """
    df = df.copy()
    df = _rename_cols(df, QUERY_COL_MAP)
    df = _fix_ctr(df)
    df = _fix_numeric(df, ['impressions', 'clicks', 'position'])

    if 'query' not in df.columns:
        raise ValueError(
            f"Could not find query column. Your columns: {list(df.columns)}\n"
            "Expected 'Top queries' or 'query' column."
        )

    df = df.dropna(subset=['query'])

    if 'impressions' in df.columns: df['impressions'] = df['impressions'].astype(int)
    if 'clicks'      in df.columns: df['clicks']      = df['clicks'].astype(int)
    if 'position'    in df.columns: df['position']    = df['position'].astype(float)
    if 'ctr'         in df.columns: df['ctr']         = df['ctr'].astype(float)

    return df.reset_index(drop=True)