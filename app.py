from __future__ import annotations

from pathlib import Path

import folium
import pandas as pd
import streamlit as st

from weather_service import DEFAULT_CSV_PATH, REGION_METADATA, load_weather_csv

DATA_PATH = Path(DEFAULT_CSV_PATH)
PAGE_TITLE = "Taiwan 7-Day Agricultural Forecast"


def _temperature_to_color(avg_temp: float) -> str:
    if avg_temp < 20:
        return "#3b82f6"
    if avg_temp <= 25:
        return "#10b981"
    if avg_temp <= 30:
        return "#f59e0b"
    return "#ef4444"


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

        [data-testid="stSidebar"] {
            background: #f7fbfa;
        }

        div[data-testid="stHorizontalBlock"] {
            align-items: stretch;
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
            max-width: 42rem;
        }

        .ranking-card {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            margin-bottom: 0.9rem;
            padding: 1.05rem 1.1rem;
        }

        .ranking-head {
            align-items: baseline;
            display: flex;
            gap: 0.8rem;
            justify-content: space-between;
        }

        .ranking-name {
            color: #102a43;
            font-size: 1rem;
            font-weight: 800;
        }

        .ranking-temp {
            color: #0f4c81;
            font-size: 1.05rem;
            font-weight: 800;
            white-space: nowrap;
        }

        .ranking-detail {
            color: #486581;
            font-size: 0.92rem;
            margin-top: 0.35rem;
        }

        .ranking-bar {
            background: #e6edf5;
            border-radius: 999px;
            height: 0.55rem;
            margin-top: 0.8rem;
            overflow: hidden;
        }

        .ranking-bar > span {
            border-radius: 999px;
            display: block;
            height: 100%;
        }

        .security-callout {
            color: #334e68;
            font-size: 0.93rem;
            line-height: 1.65;
        }

        .layout-gap {
            height: 1.35rem;
        }

        .layout-gap.tight {
            height: 0.85rem;
        }

        .stButton > button {
            background: linear-gradient(135deg, #0f766e 0%, #0f4c81 100%);
            border: none;
            border-radius: 14px;
            font-weight: 800;
            height: 3rem;
            width: 100%;
        }

        .stButton > button:disabled {
            background: #bcccdc;
            color: #52606d;
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

        [data-testid="stDataFrame"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
            overflow: hidden;
        }

        [data-testid="stAlert"] {
            border-radius: 16px;
        }

        [data-baseweb="tab-list"] {
            gap: 0.55rem;
            margin-bottom: 1rem;
        }

        button[data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 999px;
            color: #486581;
            font-weight: 700;
            padding: 0.35rem 0.95rem;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(15, 118, 110, 0.14), rgba(15, 76, 129, 0.14));
            border-color: rgba(15, 118, 110, 0.24);
            color: #0f4c81;
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
    data_state = "已載入資料" if DATA_PATH.exists() else "尚無本機 CSV"
    st.markdown(
        f"""
        <section class="hero-panel">
          <div class="hero-kicker">Agricultural Weather Dashboard</div>
          <div class="hero-title">{PAGE_TITLE}</div>
          <div class="hero-meta">
            <span class="hero-chip">資料集: CWA F-A0010-001</span>
            <span class="hero-chip">CSV 狀態: {data_state}</span>
            <span class="hero-chip">最後更新: {_format_last_updated()}</span>
            <span class="hero-chip">更新模式: 後端排程寫入快取</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _draw_temperature_map(filtered_df: pd.DataFrame, selected_date: str) -> folium.Map:
    weather_map = folium.Map(location=[23.7, 121.0], zoom_start=7, tiles="CartoDB positron")

    for _, row in filtered_df.iterrows():
        color = _temperature_to_color(float(row["avg_temp"]))
        popup_html = (
            f"<b>{row['region']}</b><br>"
            f"日期: {selected_date}<br>"
            f"最低溫: {row['min_temp']:.1f} °C<br>"
            f"最高溫: {row['max_temp']:.1f} °C<br>"
            f"平均溫: {row['avg_temp']:.1f} °C"
        )

        folium.CircleMarker(
            location=[float(row["lat"]), float(row["lon"])],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.82,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{row['region']} ({row['avg_temp']:.1f} °C)",
            weight=2,
        ).add_to(weather_map)

    legend_html = """
    <div style="
        position: fixed;
        bottom: 36px;
        left: 36px;
        z-index: 9999;
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid #d9e2ec;
        border-radius: 12px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
        padding: 12px 14px;
        font-size: 13px;
        line-height: 1.8;
    ">
      <b>平均溫度色階</b><br>
      <span style="color: #3b82f6;">●</span> &lt; 20°C<br>
      <span style="color: #10b981;">●</span> 20-25°C<br>
      <span style="color: #f59e0b;">●</span> 25-30°C<br>
      <span style="color: #ef4444;">●</span> &gt; 30°C
    </div>
    """
    weather_map.get_root().html.add_child(folium.Element(legend_html))
    return weather_map


def _render_temperature_map_html(filtered_df: pd.DataFrame, selected_date: str) -> str:
    default_center = [23.7, 121.0]
    default_zoom = 7
    weather_map = _draw_temperature_map(filtered_df, selected_date)
    map_html = weather_map.get_root().render()
    map_name = weather_map.get_name()
    reset_view_control = f"""
    <script>
      (function() {{
        const map = {map_name};
        const defaultCenter = [{default_center[0]}, {default_center[1]}];
        const defaultZoom = {default_zoom};
        const resetControl = L.control({{ position: "topleft" }});

        resetControl.onAdd = function() {{
          const container = L.DomUtil.create("div", "leaflet-bar leaflet-control");
          const button = L.DomUtil.create("a", "", container);
          button.href = "#";
          button.title = "重置地圖位置";
          button.setAttribute("aria-label", "重置地圖位置");
          button.innerHTML = "重置";
          button.style.width = "auto";
          button.style.minWidth = "58px";
          button.style.padding = "0 10px";
          button.style.background = "#ffffff";
          button.style.color = "#102a43";
          button.style.fontSize = "13px";
          button.style.fontWeight = "700";

          L.DomEvent.disableClickPropagation(container);
          L.DomEvent.on(button, "click", function(event) {{
            L.DomEvent.stop(event);
            map.setView(defaultCenter, defaultZoom);
          }});

          return container;
        }};

        resetControl.addTo(map);
      }})();
    </script>
    """
    if "</html>" in map_html:
        return map_html.replace("</html>", f"{reset_view_control}\n</html>", 1)
    return map_html + reset_view_control


def _format_table(filtered_df: pd.DataFrame) -> pd.DataFrame:
    table_df = filtered_df.copy()
    table_df = table_df[["region", "min_temp", "max_temp", "avg_temp"]]
    return table_df.rename(
        columns={
            "region": "地區",
            "min_temp": "最低溫 (°C)",
            "max_temp": "最高溫 (°C)",
            "avg_temp": "平均溫 (°C)",
        }
    )


def _build_coordinate_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"地區": name, "緯度": meta["lat"], "經度": meta["lon"]}
            for name, meta in REGION_METADATA.items()
        ]
    )


def _initialize_state() -> None:
    if "weather_df" not in st.session_state:
        st.session_state["weather_df"] = load_weather_csv(DATA_PATH)


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


def _render_summary_cards(filtered_df: pd.DataFrame, selected_date: str) -> None:
    warmest_row = filtered_df.loc[filtered_df["avg_temp"].idxmax()]
    coolest_row = filtered_df.loc[filtered_df["avg_temp"].idxmin()]
    widest_range = (filtered_df["max_temp"] - filtered_df["min_temp"]).idxmax()
    widest_range_row = filtered_df.loc[widest_range]
    regional_mean = filtered_df["avg_temp"].mean()

    card_specs = [
        (
            "區域平均",
            f"{regional_mean:.1f} °C",
            f"{selected_date} 六大區域的平均溫度概況",
        ),
        (
            "最暖區域",
            str(warmest_row["region"]),
            f"平均溫 {float(warmest_row['avg_temp']):.1f} °C",
        ),
        (
            "最涼區域",
            str(coolest_row["region"]),
            f"平均溫 {float(coolest_row['avg_temp']):.1f} °C",
        ),
        (
            "最大日溫差",
            str(widest_range_row["region"]),
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


def _render_rankings(filtered_df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">區域溫度排名</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">依平均溫度排序，快速辨識當日偏熱與偏涼區域。</div>',
        unsafe_allow_html=True,
    )

    ranking_df = filtered_df.sort_values("avg_temp", ascending=False).reset_index(drop=True)
    min_avg_temp = float(ranking_df["avg_temp"].min())
    max_avg_temp = float(ranking_df["avg_temp"].max())
    scale_span = max(max_avg_temp - min_avg_temp, 1.0)

    for _, row in ranking_df.iterrows():
        bar_width = 30 + ((float(row["avg_temp"]) - min_avg_temp) / scale_span) * 70
        color = _temperature_to_color(float(row["avg_temp"]))
        st.markdown(
            f"""
            <div class="ranking-card">
              <div class="ranking-head">
                <div class="ranking-name">{row['region']}</div>
                <div class="ranking-temp">{row['avg_temp']:.1f} °C</div>
              </div>
              <div class="ranking-detail">
                最低 {row['min_temp']:.1f} °C / 最高 {row['max_temp']:.1f} °C
              </div>
              <div class="ranking-bar">
                <span style="width: {bar_width:.1f}%; background: {color};"></span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_control_panel(available_dates: list[str]) -> str:
    controls = st.columns([1.2, 1], gap="large")

    with controls[0]:
        st.markdown('<div class="panel-label">Forecast Date</div>', unsafe_allow_html=True)
        selected_date = st.selectbox(
            "選擇日期",
            options=available_dates,
            index=0,
            label_visibility="collapsed",
        )
        st.caption("切換日期後，地圖、摘要與表格會同步更新。")

    with controls[1]:
        st.markdown(
            """
            <div class="note-card">
              <div class="panel-label">資料更新</div>
              <div class="security-callout">
                資料每 6 小時會由 Github Action 自動刷新。
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_date


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_styles()
    _initialize_state()
    _build_hero()

    dataframe = st.session_state.get("weather_df", pd.DataFrame())

    if dataframe.empty:
        st.warning("目前沒有可顯示資料。請先由後端排程執行 `fetch_weather_data.py` 產生 `weather_data.csv`。")
        st.info("前端現在只讀取快取檔案，不會自行呼叫 CWA API。")
        st.stop()

    available_dates = sorted(dataframe["date"].astype(str).unique().tolist())
    selected_date = _render_control_panel(available_dates)
    filtered_df = dataframe[dataframe["date"].astype(str) == selected_date].copy()

    if filtered_df.empty:
        st.warning("找不到該日期的資料，請改選其他日期。")
        st.stop()

    st.markdown('<div class="layout-gap"></div>', unsafe_allow_html=True)
    _render_summary_cards(filtered_df, selected_date)
    st.markdown('<div class="layout-gap"></div>', unsafe_allow_html=True)

    map_col, insight_col = st.columns([1.75, 1], gap="large")

    with map_col:
        st.markdown('<div class="section-title">地圖總覽</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">圓點顏色依平均溫度分級，點擊標記可查看當日高低溫。</div>',
            unsafe_allow_html=True,
        )
        st.components.v1.html(_render_temperature_map_html(filtered_df, selected_date), height=620, scrolling=False)

    with insight_col:
        _render_rankings(filtered_df)

    st.markdown('<div class="layout-gap"></div>', unsafe_allow_html=True)
    detail_tab, coord_tab = st.tabs(["溫度明細表", "地區座標參考"])

    with detail_tab:
        st.markdown(
            '<div class="section-copy">保留各區域最低、最高與平均溫度，方便快速比對。</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            _format_table(filtered_df),
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
            '<div class="section-copy">六大區域的近似中心座標，方便對照地圖標記位置。</div>',
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
