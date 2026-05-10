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
st.title("☁️ CODELCLOUD - DIAGNOSTIC DATA")
st.markdown('<div class="location-tag">📍 Khu Công nghiệp Gò Dầu, Long Thành, Đồng Nai</div>', unsafe_allow_html=True)

df = get_data()

if not df.empty:
    latest = df.iloc[-1]
    st.caption(f"🕒 Cập nhật: {latest['Timestamp']}")

    st.subheader("Main Monitoring")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Opacity", f"{latest['Opacity (%)']}%")
    c2.metric("Extinction", latest['Extinction'])
    c3.metric("Dust", f"{latest['Dust (mg/Nm3)']} mg/Nm3")
    c4.metric("Temp", f"{latest['Temp (C)']} °C")

    st.subheader("Technical Specs")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("DR1", latest['DR1'])
    c6.metric("DT1", latest['DT1'])
    c7.metric("DR2", latest['DR2'])
    c8.metric("DT2", latest['DT2'])

    st.subheader("Environment")
    c9, c10, c11 = st.columns(3)
    c9.metric("O2", f"{latest['O2 (%)']}%")
    c10.metric("Pressure", f"{latest['Pressure (kPa)']} kPa")
    c11.metric("H2O", f"{latest['H2O (%)']}%")

    st.markdown("---")
    with st.expander("📝 Nhật ký dữ liệu"):
        st.dataframe(df.tail(10), use_container_width=True)
else:
    st.warning("Đang kết nối dữ liệu...")

import gspread
from google.oauth2.service_account import Credentials
import datetime
import time
import random

# --- 1. KẾT NỐI GOOGLE SHEETS ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], 
    scopes=scope
)
client = gspread.authorize(creds)

try:
    sheet = client.open("QuanTracData_HeThongQuanTrac").sheet1
    print("🚀 Trình giả lập đang chạy. Dữ liệu sẽ thay đổi sau mỗi 30 giây...")
except Exception as e:
    print(f"❌ Lỗi kết nối Sheets: {e}")
    exit()

while True:
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # --- 2. TẠO GIÁ TRỊ NGẪU NHIÊN ---
        
        # Nhóm bụi và độ đục
        opacity = round(random.uniform(5.0, 15.0), 2)
        extinction = round(random.uniform(0.1, 0.8), 4)
        dust = round(random.uniform(100.0, 200.0), 1)
        
        # Nhóm khí phát thải (Dùng số 0 thay chữ O để khớp với App.py của bạn)
        s02 = round(random.uniform(25.0, 50.0), 2)
        c0 = round(random.uniform(2.0, 10.0), 2)
        c02 = round(random.uniform(10.0, 15.0), 2)
        
        # Thêm chỉ tiêu mới theo yêu cầu
        n0 = round(random.uniform(1.0, 9.0), 2)
        n02 = round(random.uniform(10.0, 30.0), 2)
        n0x = round(n0 + n02, 2)  # NOx = NO + NO2
        hcl = round(random.uniform(5.0, 15.0), 2)
        
        # Nhóm vật lý
        temp = round(random.uniform(90.0, 110.0), 1)
        flow = round(random.uniform(4500, 6000), 0)
        pressure = round(random.uniform(100, 105), 0)
        o2 = round(random.uniform(5.0, 8.0), 1)
        h2o = round(random.uniform(12.0, 15.0), 1)
        
        # Thông số kỹ thuật thiết bị
        dr1 = random.randint(10000, 10100)
        dt1 = random.randint(10050, 10150)
        dr2 = random.randint(9900, 10050)
        dt2 = random.randint(10000, 10100)

        # --- 3. ĐÓNG GÓI DỮ LIỆU ---
        # Danh sách này phải khớp 100% với số lượng và thứ tự cột trên Google Sheets
        row = [
            now,           # Cột A: Timestamp
            opacity,       # Cột B: Opacity (%)
            extinction,    # Cột C: Extinction
            dust,          # Cột D: Dust (mg/Nm3)
            temp,          # Cột E: Temp (C)
            flow,          # Cột F: Flow (m3/h)
            o2,            # Cột G: O2 (%)
            pressure,      # Cột H: Pressure (kPa)
            h2o,           # Cột I: H2O (%)
            s02,           # Cột J: S02 (mg/Nm3)
            c0,            # Cột K: C0 (mg/Nm3)
            c02,           # Cột L: C02 (mg/Nm3)
            n02,           # Cột M: N02 (mg/Nm3)
            n0x,           # Cột N: N0X (mg/Nm3)
            0,             # Cột O: Misalignment (%)
            0,             # Cột P: Delta Opacity (%)
            "Valid",       # Cột Q: Detector Valid
            "On",          # Cột R: Plant Status
            dr1,           # Cột S: DR1
            dt1,           # Cột T: DT1
            dr2,           # Cột U: DR2
            dt2,           # Cột V: DT2
            hcl,           # Cột W: HCl
            n0             # Cột X: N0
        ]
        
        # Gửi dữ liệu
        sheet.append_row(row)
        
        # In thông báo ra màn hình (Sửa lỗi f-string)
        print(f"✅ [{now}] Cập nhật: Dust={dust}, SO2={s02}, NO={n0}, NO2={n02}, NOx={n0x}, HCl={hcl}")
        
        # Đợi 30 giây
        time.sleep(30)
        
    except Exception as e:
        print(f"⚠️ Đang thử lại do lỗi: {e}")
