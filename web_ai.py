import streamlit as st
import requests
import json

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="AI Super Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS TRANG TRÍ ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stChatInput {
        position: fixed;
        bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- THANH MENU BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Cấu hình AI")
    
    # --- PHẦN SỬA LỖI QUAN TRỌNG: LẤY KEY AN TOÀN ---
    MY_API_KEY = None
    try:
        # Thử tìm két sắt bí mật (chỉ chạy được khi đã lên Cloud)
        if "GOOGLE_API_KEY" in st.secrets:
            MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
            st.success("✅ Đã kết nối Key từ hệ thống")
    except FileNotFoundError:
        # Nếu chạy trên máy cá nhân mà không có file secrets -> Bỏ qua lỗi này
        pass
    except Exception:
        pass
        
    # Nếu không tìm thấy Key trong két sắt, hiện ô nhập thủ công
    if not MY_API_KEY:
        st.warning("⚠️ Đang chạy trên máy cá nhân")
        MY_API_KEY = st.text_input("Dán API Key của bạn:", type="password")
    # ---------------------------------------------------

    st.divider()
    
    # Chọn tính cách
    st.subheader("🎭 Chọn vai diễn")
    tinh_cach = st.radio(
        "Bạn muốn AI nói chuyện kiểu gì?",
        ["Bà hàng xóm đanh đá 🤬", "Trợ lý chuyên nghiệp 👔", "Người yêu nhõng nhẽo 🥰", "Dân chơi Hip-hop 🧢"]
    )
    
    st.divider()
    
    # Nút xóa
    if st.button("🗑️ Xóa sạch cuộc trò chuyện"):
        st.session_state.messages = []
        st.rerun()

# --- HÀM GỌI API ---
def hoi_gemini(lich_su_chat, kieu_noi_chuyen):
    if not MY_API_KEY:
        return "Vui lòng nhập API Key ở thanh bên trái trước nhé! 👈"
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={MY_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Xử lý lịch sử chat
    google_history = []
    for msg in lich_su_chat:
        role = "user" if msg["role"] == "user" else "model"
        google_history.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    # Gắn nhân cách
    prompts = {
        "Bà hàng xóm đanh đá 🤬": "Bạn là bà hàng xóm nhiều chuyện, đanh đá, hay dùng icon. Trả lời ngắn gọn.",
        "Trợ lý chuyên nghiệp 👔": "Bạn là trợ lý ảo lịch sự, dùng kính ngữ, trả lời chi tiết và gãy gọn.",
        "Người yêu nhõng nhẽo 🥰": "Bạn là người yêu dễ thương, hay dỗi, gọi người dùng là 'anh yêu' hoặc 'chồng ơi'.",
        "Dân chơi Hip-hop 🧢": "Bạn là Rapper, nói chuyện gieo vần, dùng từ lóng giới trẻ (Bro, Homie)."
    }
    
    system_instruction = {
        "role": "user",
        "parts": [{"text": f"HÃY NHỚ: {prompts[kieu_noi_chuyen]}"}]
    }
    google_history.insert(0, system_instruction)

    data = { "contents": google_history }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Lỗi Google: {response.text}"
    except Exception as e:
        return f"Lỗi: {e}"

# --- GIAO DIỆN CHÍNH ---
st.title("💬 Chat cùng AI Đa Nhân Cách")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiện tin nhắn
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Nhập liệu
if prompt := st.chat_input("Nói gì đi bro..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner(f"{tinh_cach} đang soạn tin..."):
            response = hoi_gemini(st.session_state.messages, tinh_cach)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})