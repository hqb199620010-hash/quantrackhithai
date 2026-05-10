import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="CodelCloud Monitoring", layout="wide")

# Tự động làm mới mỗi 30 giây
st_autorefresh(interval=30 * 1000, key="datarefresh")

# --- 2. GIAO DIỆN CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #87CEEB; }
    .location-tag, .time-text {
        background-color: #003366; color: white !important; padding: 8px 20px;
        border-radius: 50px; font-weight: bold; display: inline-block;
        margin-bottom: 20px; box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
    }
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.7) !important;
        border: 4px solid #002D54 !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. KẾT NỐI GOOGLE SHEETS (Dùng st.cache để app chạy nhanh hơn) ---
@st.cache_resource
def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scope
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Lỗi cấu hình Secrets: {e}")
        return None

client = init_connection()

def get_data():
    if client is None: return pd.DataFrame()
    try:
        # Mở đúng tên file Google Sheets của bạn
        sheet = client.open("QuanTracData_HeThongQuanTrac").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Không thể lấy dữ liệu từ Sheets: {e}")
        return pd.DataFrame()

# --- 4. HIỂN THỊ ---
st.title("☁️ CODELCLOUD - MONITORING")
st.markdown('<div class="location-tag">📍 Khu Công nghiệp Gò Dầu, Long Thành, Đồng Nai</div>', unsafe_allow_html=True)

df = get_data()

if not df.empty:
    latest = df.iloc[-1]
    st.markdown(f"<div class='time-text'>🕒 Cập nhật: {latest.get('Timestamp', 'N/A')}</div>", unsafe_allow_html=True)

    st.subheader("📊 Thông số chính")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Opacity", f"{latest.get('Opacity (%)', 0)}%")
    c2.metric("Extinction", latest.get('Extinction', 0))
    c3.metric("Dust", f"{latest.get('Dust (mg/Nm3)', 0)} mg/m3")
    c4.metric("Temp", f"{latest.get('Temp (C)', 0)} °C")

    st.subheader("🌍 Môi trường & Khí thải")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("O2", f"{latest.get('O2 (%)', 0)}%")
    c6.metric("SO2", f"{latest.get('S02 (mg/Nm3)', 0)}")
    c7.metric("NOx", f"{latest.get('N0X (mg/Nm3)', 0)}")
    c8.metric("Pressure", f"{latest.get('Pressure (kPa)', 0)} kPa")

    st.markdown("---")
    with st.expander("📝 Nhật ký 10 bản ghi gần nhất"):
        st.dataframe(df.tail(10), use_container_width=True)
else:
    st.info("Hệ thống đang kết nối dữ liệu, vui lòng đợi giây lát...")
