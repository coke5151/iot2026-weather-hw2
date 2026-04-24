from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from weather_service import (
    DEFAULT_DB_PATH,
    REGION_METADATA,
    get_available_regions,
    load_region_forecast,
)

DATA_PATH = Path(DEFAULT_DB_PATH)
PAGE_TITLE = "Taiwan 7-Day Agricultural Forecast"


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: "Noto Sans TC", "Microsoft JhengHei", "Segoe UI", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(15, 118, 110, 0.14), transparent 24%),
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 20%),
                linear-gradient(180deg, #f4f8f7 0%, #f8fafc 56%, #ffffff 100%);
        }

        [data-testid="stAppViewContainer"] > .main {
            padding-top: 1.25rem;
        }

        .block-container {
            max-width: 1320px;
            padding: 1.1rem 1.4rem 4rem;
        }

        .hero-panel {
            background: linear-gradient(135deg, rgba(15, 118, 110, 0.98), rgba(15, 76, 129, 0.94));
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 28px;
            box-shadow: 0 24px 64px rgba(15, 23, 42, 0.14);
            color: #ffffff;
            margin-bottom: 1.35rem;
            padding: 2.15rem 2.35rem;
        }

        .hero-kicker {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            opacity: 0.8;
            text-transform: uppercase;
        }

        .hero-title {
            font-size: 2.35rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            line-height: 1.05;
            margin: 0.4rem 0 0.8rem;
        }

        .hero-subtitle {
            font-size: 1rem;
            line-height: 1.7;
            max-width: 52rem;
            opacity: 0.94;
        }

        .hero-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.85rem;
            margin-top: 1.35rem;
        }

        .hero-chip {
            background: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 999px;
            font-size: 0.92rem;
            padding: 0.55rem 0.84rem;
        }

        .panel-label {
            color: #486581;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin-bottom: 0.45rem;
            text-transform: uppercase;
        }

        .note-card {
            background: linear-gradient(180deg, #f8fafc 0%, #eef7f5 100%);
            border: 1px solid rgba(15, 118, 110, 0.12);
            border-radius: 18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
            color: #243b53;
            font-size: 0.95rem;
            line-height: 1.7;
            padding: 0.9rem 1.05rem;
        }

        .summary-card {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 20px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
            min-height: 148px;
            padding: 1.2rem 1.25rem;
        }

        .summary-label {
            color: #627d98;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .summary-value {
            color: #102a43;
            font-size: 1.65rem;
            font-weight: 800;
            line-height: 1.2;
            margin-top: 0.45rem;
        }

        .summary-detail {
            color: #486581;
            font-size: 0.94rem;
            line-height: 1.55;
            margin-top: 0.35rem;
        }

        .section-title {
            color: #102a43;
            font-size: 1.16rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .section-copy {
            color: #627d98;
            line-height: 1.6;
            margin-bottom: 1.05rem;
            max-width: 46rem;
        }

        .insight-card {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
            padding: 1.1rem 1.15rem;
        }

        .insight-title {
            color: #102a43;
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.8rem;
        }

        .insight-item {
            color: #334e68;
            font-size: 0.95rem;
            line-height: 1.75;
            margin-bottom: 0.35rem;
        }

        .layout-gap {
            height: 1.35rem;
        }

        .layout-gap.tight {
            height: 0.85rem;
        }

        div[data-testid="stSelectbox"] > label {
            color: #334e68;
            font-weight: 700;
        }

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.12);
            border-radius: 14px;
            min-height: 3rem;
        }

        [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
            overflow: hidden;
        }

        [data-testid="stAlert"] {
            border-radius: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_last_updated() -> str:
    if not DATA_PATH.exists():
        return "尚未建立"
    return pd.Timestamp(DATA_PATH.stat().st_mtime, unit="s").strftime("%Y-%m-%d %H:%M")


def _build_hero() -> None:
    data_state = "已載入資料庫" if DATA_PATH.exists() else "尚無本機 SQLite"
    st.markdown(
        f"""
        <section class="hero-panel">
          <div class="hero-kicker">Agricultural Weather Dashboard</div>
          <div class="hero-title">{PAGE_TITLE}</div>
          <div class="hero-subtitle">
            依作業需求提供六大區域下拉選單、一週氣溫折線圖與明細表，
            前端資料統一由 SQLite 查詢，不直接讀取 CSV。
          </div>
          <div class="hero-meta">
            <span class="hero-chip">資料集: CWA F-A0010-001</span>
            <span class="hero-chip">SQLite 狀態: {data_state}</span>
            <span class="hero-chip">最後更新: {_format_last_updated()}</span>
            <span class="hero-chip">更新模式: 後端排程同步更新 CSV + data.db</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _format_short_date(date_text: str) -> str:
    return pd.Timestamp(date_text).strftime("%m/%d")


def _render_control_panel(available_regions: list[str]) -> str:
    controls = st.columns([1.2, 1], gap="large")

    with controls[0]:
        st.markdown('<div class="panel-label">Region Selector</div>', unsafe_allow_html=True)
        selected_region = st.selectbox(
            "選擇地區",
            options=available_regions,
            index=0,
            label_visibility="collapsed",
        )
        st.caption("切換地區後，折線圖、摘要卡與一週資料表會同步更新。")

    with controls[1]:
        st.markdown(
            """
            <div class="note-card">
              <div class="panel-label">資料來源</div>
              本頁面只查詢本機 SQLite 快取，不會在前端直接呼叫 CWA API。
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_region


def _render_summary_card(title: str, value: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="summary-card">
          <div class="summary-label">{title}</div>
          <div class="summary-value">{value}</div>
          <div class="summary-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_summary_cards(forecast_df: pd.DataFrame) -> None:
    warmest_row = forecast_df.loc[forecast_df["avg_temp"].idxmax()]
    coolest_row = forecast_df.loc[forecast_df["avg_temp"].idxmin()]
    widest_range_index = (forecast_df["max_temp"] - forecast_df["min_temp"]).idxmax()
    widest_range_row = forecast_df.loc[widest_range_index]
    weekly_mean = forecast_df["avg_temp"].mean()

    card_specs = [
        (
            "一週平均",
            f"{weekly_mean:.1f} °C",
            "依七日平均溫度整體觀察氣溫走勢。",
        ),
        (
            "最暖日",
            _format_short_date(str(warmest_row["date"])),
            f"平均溫 {float(warmest_row['avg_temp']):.1f} °C",
        ),
        (
            "最涼日",
            _format_short_date(str(coolest_row["date"])),
            f"平均溫 {float(coolest_row['avg_temp']):.1f} °C",
        ),
        (
            "最大日溫差",
            _format_short_date(str(widest_range_row["date"])),
            f"高低溫差 {float(widest_range_row['max_temp'] - widest_range_row['min_temp']):.1f} °C",
        ),
    ]

    for row_index in range(0, len(card_specs), 2):
        cards = st.columns(2, gap="large")
        for column, (title, value, detail) in zip(cards, card_specs[row_index : row_index + 2]):
            with column:
                _render_summary_card(title, value, detail)
        if row_index + 2 < len(card_specs):
            st.markdown('<div class="layout-gap tight"></div>', unsafe_allow_html=True)


def _build_chart_data(forecast_df: pd.DataFrame) -> pd.DataFrame:
    chart_df = forecast_df.copy()
    chart_df["日期"] = chart_df["date"].map(_format_short_date)
    return chart_df.rename(
        columns={
            "min_temp": "最低溫 (°C)",
            "avg_temp": "平均溫 (°C)",
            "max_temp": "最高溫 (°C)",
        }
    )[["日期", "最低溫 (°C)", "平均溫 (°C)", "最高溫 (°C)"]]


def _render_weekly_chart(forecast_df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">一週氣溫折線圖</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">同時比較最低溫、平均溫與最高溫，對照七天內的升降變化。</div>',
        unsafe_allow_html=True,
    )
    st.line_chart(
        _build_chart_data(forecast_df),
        x="日期",
        y=["最低溫 (°C)", "平均溫 (°C)", "最高溫 (°C)"],
        height=380,
        use_container_width=True,
    )


def _render_region_insights(selected_region: str, forecast_df: pd.DataFrame) -> None:
    metadata = REGION_METADATA[selected_region]
    start_date = _format_short_date(str(forecast_df["date"].min()))
    end_date = _format_short_date(str(forecast_df["date"].max()))
    weekly_low = forecast_df["min_temp"].min()
    weekly_high = forecast_df["max_temp"].max()
    steady_days = int((forecast_df["avg_temp"].diff().abs().fillna(0) <= 1.0).sum())

    st.markdown('<div class="section-title">區域重點</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-title">{selected_region}</div>
          <div class="insight-item">預報期間: {start_date} - {end_date}</div>
          <div class="insight-item">近似中心座標: {metadata['lat']:.2f}, {metadata['lon']:.2f}</div>
          <div class="insight-item">一週最低溫: {weekly_low:.1f} °C</div>
          <div class="insight-item">一週最高溫: {weekly_high:.1f} °C</div>
          <div class="insight-item">溫度相對平穩天數: {steady_days} 天</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_table(forecast_df: pd.DataFrame) -> pd.DataFrame:
    table_df = forecast_df.copy()
    table_df["date"] = table_df["date"].map(_format_short_date)
    return table_df.rename(
        columns={
            "date": "日期",
            "region": "地區",
            "min_temp": "最低溫 (°C)",
            "max_temp": "最高溫 (°C)",
            "avg_temp": "平均溫 (°C)",
        }
    )[["日期", "地區", "最低溫 (°C)", "最高溫 (°C)", "平均溫 (°C)"]]


def _build_coordinate_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"地區": name, "緯度": meta["lat"], "經度": meta["lon"]}
            for name, meta in REGION_METADATA.items()
        ]
    )


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_styles()
    _build_hero()

    available_regions = get_available_regions(DATA_PATH)
    if not available_regions:
        st.warning("目前沒有可顯示資料。請先由後端執行 `fetch_weather_data.py` 產生 `data.db`。")
        st.info("前端現在只讀取 SQLite 快取，不會自行呼叫 CWA API。")
        st.stop()

    selected_region = _render_control_panel(available_regions)
    forecast_df = load_region_forecast(selected_region, DATA_PATH)

    if forecast_df.empty:
        st.warning("找不到該地區的預報資料，請改選其他地區。")
        st.stop()

    st.markdown('<div class="layout-gap"></div>', unsafe_allow_html=True)
    _render_summary_cards(forecast_df)
    st.markdown('<div class="layout-gap"></div>', unsafe_allow_html=True)

    chart_col, insight_col = st.columns([1.75, 1], gap="large")
    with chart_col:
        _render_weekly_chart(forecast_df)
    with insight_col:
        _render_region_insights(selected_region, forecast_df)

    st.markdown('<div class="layout-gap"></div>', unsafe_allow_html=True)
    detail_tab, coord_tab = st.tabs(["一週預報表", "地區座標參考"])

    with detail_tab:
        st.markdown(
            '<div class="section-copy">列出所選地區未來七天的最低溫、最高溫與平均溫。</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            _format_table(forecast_df),
            use_container_width=True,
            hide_index=True,
            column_config={
                "最低溫 (°C)": st.column_config.NumberColumn(format="%.1f"),
                "最高溫 (°C)": st.column_config.NumberColumn(format="%.1f"),
                "平均溫 (°C)": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    with coord_tab:
        st.markdown(
            '<div class="section-copy">六大區域的近似中心座標，可對照地區範圍與資料來源設定。</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            _build_coordinate_table(),
            use_container_width=True,
            hide_index=True,
            column_config={
                "緯度": st.column_config.NumberColumn(format="%.2f"),
                "經度": st.column_config.NumberColumn(format="%.2f"),
            },
        )


if __name__ == "__main__":
    main()
