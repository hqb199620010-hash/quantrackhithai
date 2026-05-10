import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="CodelCloud Monitoring", layout="wide")

# Tự động làm mới mỗi 30 giây
st_autorefresh(interval=30 * 1000, key="datarefresh")

# --- 2. TÙY CHỈNH GIAO DIỆN (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #87CEEB; }
    h1 { color: #002D54 !important; font-weight: 850 !important; }
    .location-tag {
        background-color: #003366; color: white !important; padding: 8px 20px;
        border-radius: 50px; font-weight: bold; display: inline-block;
        margin-bottom: 25px; box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
    }
    .time-text {
        background-color: #003366; color: white !important; padding: 8px 20px;
        border-radius: 50px; font-weight: bold; display: inline-block;
        margin-bottom: 25px; box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
    }
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.7) !important;
        border: 4px solid #002D54 !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. KẾT NỐI GOOGLE SHEETS ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scope
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi xác thực Google: {e}")
        return None

client = get_gspread_client()

# --- 4. HÀM LẤY DỮ LIỆU ---
def get_data():
    if client is None:
        return pd.DataFrame()
    try:
        # Mở bằng tên file chính xác của bạn
        sheet = client.open("QuanTracData_HeThongQuanTrac").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi truy cập bảng tính: {e}")
        return pd.DataFrame()

# --- 5. HIỂN THỊ GIAO DIỆN ---
st.title("☁️ CODELCLOUD - MONITORING")
st.markdown('<div class="location-tag">📍 Khu Công nghiệp Gò Dầu, Long Thành, Đồng Nai</div>', unsafe_allow_html=True)

df = get_data()

if not df.empty:
    latest = df.iloc[-1]
    
    st.markdown(f"<div class='time-text'>🕒 Cập nhật: {latest.get('Timestamp', 'N/A')}</div>", unsafe_allow_html=True)

    st.subheader("Main Monitoring")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Opacity", f"{latest.get('Opacity (%)', 0)}%")
    c2.metric("Extinction", latest.get('Extinction', 0))
    c3.metric("Dust", f"{latest.get('Dust (mg/Nm3)', 0)} mg/m3")
    c4.metric("Temp", f"{latest.get('Temp (C)', 0)} °C")

    st.subheader("Environment")
    c5, c6, c7 = st.columns(3)
    c5.metric("O2", f"{latest.get('O2 (%)', 0)}%")
    c6.metric("Pressure", f"{latest.get('Pressure (kPa)', 0)} kPa")
    c7.metric("H2O", f"{latest.get('H2O (%)', 0)}%")

    st.markdown("---")
    with st.expander("📝 Nhật ký dữ liệu (10 bản ghi gần nhất)"):
        st.dataframe(df.tail(10), use_container_width=True)
else:
    st.info("Đang chờ dữ liệu mới từ hệ thống...")
