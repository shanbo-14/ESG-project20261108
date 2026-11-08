import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# ------------------------------------------------------------------
# 頁面設定
# ------------------------------------------------------------------
st.set_page_config(page_title="公開資訊資料檢視", page_icon="📊", layout="wide")

DEFAULT_URL = "https://mopsfin.twse.com.tw/opendata/t187ap46_O_1.csv"


# ------------------------------------------------------------------
# 資料讀取（快取 1 小時，避免每次互動都重新下載）
# ------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(url: str, verify_ssl: bool = True) -> pd.DataFrame:
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = requests.get(url, verify=verify_ssl, timeout=30)
    response.raise_for_status()

    # utf-8-sig 可處理繁體中文與 BOM
    df = pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")
    df = df.dropna()
    return df


# ------------------------------------------------------------------
# 側邊欄
# ------------------------------------------------------------------
st.sidebar.header("設定")
url = st.sidebar.text_input("CSV 連結", value=DEFAULT_URL)
verify_ssl = st.sidebar.checkbox(
    "驗證 SSL 憑證",
    value=True,
    help="若連線出現 SSL 錯誤，可取消勾選（等同原程式的 verify=False，安全性較低）。",
)
if st.sidebar.button("重新載入資料"):
    st.cache_data.clear()

# ------------------------------------------------------------------
# 主畫面
# ------------------------------------------------------------------
st.title("📊 公開資訊資料檢視")
st.caption(f"資料來源：{url}")

try:
    with st.spinner("資料下載中..."):
        df = load_data(url, verify_ssl)
except requests.exceptions.SSLError:
    st.error("SSL 憑證驗證失敗，請到左側取消勾選「驗證 SSL 憑證」後再試。")
    st.stop()
except Exception as e:
    st.error(f"資料讀取失敗：{e}")
    st.stop()

# 關鍵字搜尋
keyword = st.text_input("🔍 關鍵字搜尋（會搜尋所有欄位）")
if keyword:
    mask = df.astype(str).apply(
        lambda col: col.str.contains(keyword, case=False, na=False)
    ).any(axis=1)
    view_df = df[mask]
else:
    view_df = df

col1, col2 = st.columns(2)
col1.metric("總筆數", f"{len(df):,}")
col2.metric("目前顯示筆數", f"{len(view_df):,}")

st.dataframe(view_df, use_container_width=True, hide_index=True)

# 下載（加 BOM，Excel 開啟繁體中文不會亂碼）
csv_bytes = view_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="⬇️ 下載 CSV",
    data=csv_bytes,
    file_name="data01.csv",
    mime="text/csv",
)
