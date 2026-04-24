from __future__ import annotations

import os
from pathlib import Path

import folium
import pandas as pd
import streamlit as st

from weather_service import DEFAULT_CSV_PATH, REGION_METADATA, load_weather_csv, save_weather_csv

DATA_PATH = Path(DEFAULT_CSV_PATH)


def _temperature_to_color(avg_temp: float) -> str:
    if avg_temp < 20:
        return "blue"
    if avg_temp <= 25:
        return "green"
    if avg_temp <= 30:
        return "yellow"
    return "red"


def _get_default_api_key() -> str:
    secret_key = ""
    try:
        secret_key = st.secrets.get("CWA_API_KEY", "")
    except Exception:
        secret_key = ""
    return os.getenv("CWA_API_KEY", secret_key).strip()


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
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{row['region']} ({row['avg_temp']:.1f} °C)",
        ).add_to(weather_map)

    legend_html = """
    <div style="
        position: fixed;
        bottom: 40px;
        left: 40px;
        z-index: 9999;
        background: white;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 13px;
        line-height: 1.7;
    ">
      <b>平均溫度色階</b><br>
      <span style="color: blue;">●</span> &lt; 20°C<br>
      <span style="color: green;">●</span> 20-25°C<br>
      <span style="color: #d6a600;">●</span> 25-30°C<br>
      <span style="color: red;">●</span> &gt; 30°C
    </div>
    """
    weather_map.get_root().html.add_child(folium.Element(legend_html))
    return weather_map


def _format_table(filtered_df: pd.DataFrame) -> pd.DataFrame:
    table_df = filtered_df.copy()
    table_df = table_df[["region", "min_temp", "max_temp", "avg_temp"]]
    table_df = table_df.rename(
        columns={
            "region": "地區",
            "min_temp": "最低溫 (°C)",
            "max_temp": "最高溫 (°C)",
            "avg_temp": "平均溫 (°C)",
        }
    )
    return table_df


def _initialize_state() -> None:
    if "weather_df" not in st.session_state:
        st.session_state["weather_df"] = load_weather_csv(DATA_PATH)


def _fetch_latest_data(api_key: str) -> None:
    dataframe = save_weather_csv(DATA_PATH, api_key=api_key)
    st.session_state["weather_df"] = dataframe


def main() -> None:
    st.set_page_config(page_title="Taiwan 7-Day Agricultural Forecast", layout="wide")
    st.title("Taiwan 7-Day Agricultural Forecast (CWA F-A0010-001)")
    st.caption("地圖使用近似地區座標，並依平均溫度以顏色區分。")

    _initialize_state()

    with st.sidebar:
        st.header("資料更新")
        default_key = _get_default_api_key()
        api_key = st.text_input("CWA API Key", value=default_key, type="password")
        st.caption("部署到 Streamlit Cloud 可在 Secrets 設定 CWA_API_KEY。")

        if st.button("從 CWA 重新抓取資料", type="primary"):
            try:
                _fetch_latest_data(api_key)
                st.success(f"已更新資料並輸出至 {DATA_PATH.resolve()}")
            except Exception as exc:
                st.error(str(exc))

    dataframe = st.session_state.get("weather_df", pd.DataFrame())
    if dataframe.empty:
        st.warning("目前沒有可顯示資料。請在左側輸入 CWA API Key 後更新資料。")
        st.info(
            "若遇到 SSL 憑證問題，系統會自動回退至 verify=False 重新請求。"
        )
        st.stop()

    available_dates = sorted(dataframe["date"].astype(str).unique().tolist())
    selected_date = st.selectbox("選擇日期", options=available_dates, index=0)
    filtered_df = dataframe[dataframe["date"].astype(str) == selected_date].copy()

    left_col, right_col = st.columns([3, 2], gap="large")

    with left_col:
        st.subheader(f"地圖檢視 - {selected_date}")
        weather_map = _draw_temperature_map(filtered_df, selected_date)
        st.components.v1.html(weather_map.get_root().render(), height=620, scrolling=False)

    with right_col:
        st.subheader(f"溫度資料表 - {selected_date}")
        table_df = _format_table(filtered_df)
        st.dataframe(table_df, use_container_width=True, hide_index=True)

        st.markdown("**地區座標 (近似值)**")
        coordinate_df = pd.DataFrame(
            [
                {"地區": name, "緯度": meta["lat"], "經度": meta["lon"]}
                for name, meta in REGION_METADATA.items()
            ]
        )
        st.dataframe(coordinate_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
