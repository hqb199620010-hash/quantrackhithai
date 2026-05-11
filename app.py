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
    /* Nền toàn trang xanh nhạt */
    .stApp {
        background-color: #FFFFFF;
    }

    /* Tiêu đề chính */
    h1 {
        color: #002D54 !important;
        font-weight: 850 !important;
    }

    /* Tag địa chỉ nổi bật */
    .location-tag {
        background-color: #003366;
        color: white !important;
        padding: 8px 20px;
        border-radius: 50px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 25px;
        box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
    }

	.Timestamp{
        background-color: #003366;
        color: white !important;
        padding: 8px 20px;
        border-radius: 50px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 25px;
        box-shadow: 3px 3px 10px rgba(0,0,0,0.2);
    }



    /* SỬA LỖI CHỮ TRẮNG/MỜ: ÉP MÀU XANH CHO CÁC TIÊU ĐỀ PHỤ */
    /* Chúng ta nhắm vào tất cả các cấp độ tiêu đề và div chứa subheader */
    [data-testid="stSubheader"] h3, 
    [data-testid="stMarkdownContainer"] h3,
    .stSubheader h3 {
        color: #002D54 !important;      /* Màu xanh Navy đậm */
        opacity: 1 !important;           /* Loại bỏ độ mờ của Streamlit */
        font-weight: 900 !important;     /* Độ đậm cực cao */
        font-size: 26px !important;
        text-transform: uppercase !important;
        border-left: 6px solid #0056B3 !important;
        padding-left: 15px !important;
        display: block !important;
    }

    /* Metric Card trắng bo tròn */
    div[data-testid="metric-container"] {
	color: #003366
        background-color: #003366 !important;
	opacity: 1; 
        border: 1px solid #003366 !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 5px 5px 15px rgba(0, 45, 84, 0.08) !important;
    }

    /* Số liệu màu xanh dương */
    [data-testid="stMetricValue"] {
        color: #003366 !important;
	opacity: 1
        font-size: 2.5rem !important;
        font-weight: 800 !important;
	display: block
    }

    /* Tên các chỉ tiêu */
    [data-testid="stMetricLabel"] {
        color: #003366 !important;
        font-weight: 700 !important;
	opacity: 1
	display: block

    }
/* ĐOẠN CODE GIỮ NỀN TRẮNG TUYỆT ĐỐI CHO NHẬT KÝ */

    /* 1. Ép nền trắng cố định cho khung Nhật ký (Expander) ở mọi trạng thái */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D9E6 !important;
        border-radius: 12px !important;
    }

    /* 2. Loại bỏ hiệu ứng đổi màu khi di chuột vào (Hover) và khi click (Active) */
    div[data-testid="stExpander"]:hover, 
    div[data-testid="stExpander"]:active,
    div[data-testid="stExpander"]:focus-within {
        background-color: #FFFFFF !important;
        border: 1px solid #0056B3 !important; /* Viền xanh đậm hơn một chút khi tương tác */
    }

    /* 3. Đảm bảo phần tiêu đề chữ luôn hiển thị rõ trên nền trắng */
    div[data-testid="stExpander"] summary p {
        color: #003366 !important;
        font-weight: bold !important;
    }

    /* 4. Loại bỏ lớp phủ màu mặc định của Streamlit trên phần Summary */
    div[data-testid="stExpander"] summary {
        background-color: transparent !important;
    }
    
    div[data-testid="stExpander"] summary:hover {
        background-color: transparent !important;
    }
/* TẠO Ô CHỨA CHỈ TIÊU MÀU XANH DƯƠNG NỔI BẬT */
    div[data-testid="metric-container"] {
        background-color: #003366 !important; /* Nền xanh dương nổi bật */
        border: 1px solid #003366 !important;
        padding: 20px !important;
        border-radius: 15px !important;
        box-shadow: 0px 4px 15px rgba(0, 45, 84, 0.3) !important; /* Đổ bóng đậm hơn */
        transition: transform 0.2s ease-in-out;
    }

    /* Hiệu ứng phóng nhẹ khi đưa chuột vào ô chỉ tiêu */
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0px 8px 20px rgba(0, 45, 84, 0.4) !important;
    }

    /* Đổi chữ của Con số dữ liệu sang màu TRẮNG để nổi trên nền xanh */
    [data-testid="stMetricValue"] {
        color: ##003366 !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }

    /* Đổi chữ của Tên chỉ tiêu (Label) sang màu TRẮNG NHẠT */
    [data-testid="stMetricLabel"] {
        color: #003366 !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HÀM LẤY DỮ LIỆU ---
def get_data():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], 
    scopes=scope
)
        client = gspread.authorize(creds)
        sheet = client.open("QuanTracData_HeThongQuanTrac").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame()

# --- 4. HIỂN THỊ ---
st.title("☁️ 5S - SOFTWARE")
st.markdown('<div class="location-tag">📍 Lô số 7, Khu xử lý chất thải tập trung Tóc Tiên, Xã Châu Pha, Tp Hồ Chí Minh, Việt Nam</div>', unsafe_allow_html=True)

df = get_data()
if not df.empty:
    latest = df.iloc[-1]
    st.caption(f"🕒 Cập nhật: {latest['Timestamp']}")

    st.subheader("Main Monitoring")
    
    c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12 = st.columns(12)
    c1.metric("Dust", f"{latest['# Dust (mg/Nm3)']} mg/Nm3")
    c2.metric("Temp", f"{latest['# Temp (C)']} °C")
    c3.metric("O2", f"{latest['# O2 (%)']}%")
    c4.metric("Pressure", f"{latest['# Pressure (kPa)']} kPa")
    c5.metric("H2O", f"{latest['# H2O (%)']}%")


    c6.metric("SO2", f"{latest['# SO2 (mg/Nm3)']} mg/Nm3")
    c7.metric("CO", f"{latest['# CO (mg/Nm3)']} mg/Nm3")
    c8.metric("CO2", f"{latest['# CO2 (mg/Nm3)']} mg/Nm3")
    c9.metric("NO2", f"{latest['# NO2 (mg/Nm3)']} mg/Nm3")
    c10.metric("NOx", f"{latest['# NOX (mg/Nm3)']} mg/Nm3")


    c11.metric("HCl", f"{latest['# HCl']} mg/Nm3")
    c12.metric("NO", f"{latest['# NO']} mg/Nm3")

    st.markdown("---")
    with st.expander("📝 Nhật ký dữ liệu"):
        st.dataframe(df.tail(10), use_container_width=True)

else:
    # Lệnh else này phải thẳng hàng tuyệt đối với lệnh 'if not df.empty:' ở trên
    st.warning("Đang kết nối dữ liệu...")
