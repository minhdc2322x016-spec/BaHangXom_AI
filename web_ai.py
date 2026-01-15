import streamlit as st
import requests
import json
import base64

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="Ultimate AI Chat",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS TÙY CHỈNH GIAO DIỆN ---
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

# --- 2. THANH MENU BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.header("🎛️ Trung tâm điều khiển")
    
    # --- A. KẾT NỐI API KEY (AN TOÀN) ---
    MY_API_KEY = None
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
            st.success("✅ Đã kết nối Key từ hệ thống")
    except Exception:
        pass
        
    if not MY_API_KEY:
        st.warning("⚠️ Đang chạy trên máy cá nhân")
        MY_API_KEY = st.text_input("Dán API Key của bạn:", type="password")
    
    st.divider()

    # --- B. CHỌN NHÂN VẬT & AVATAR ---
    st.subheader("🎭 Chọn Nhân Cách")
    tinh_cach = st.radio(
        "AI sẽ đóng vai ai?",
        ["Bà hàng xóm 👵", "Trợ lý ảo 🤖", "Em yêu 😽", "Rapper 🎧"]
    )
    
    # Map nhân vật với Emoji để làm Avatar
    avatar_map = {
        "Bà hàng xóm 👵": "👵",
        "Trợ lý ảo 🤖": "🤖",
        "Em yêu 😽": "😽",
        "Rapper 🎧": "🎧"
    }
    current_avatar = avatar_map[tinh_cach]

    st.divider()

    # --- C. THANH NHIỆT ĐỘ (CREATIVITY) ---
    st.subheader("🌡️ Độ Sáng Tạo")
    do_sang_tao = st.slider(
        "Thấp (Nghiêm túc) <-> Cao (Bay bổng)", 
        min_value=0.0, max_value=2.0, value=1.0, step=0.1
    )
    st.caption(f"Mức độ hiện tại: {do_sang_tao}")

    st.divider()

    # --- D. UPLOAD ẢNH (MẮT THẦN) ---
    st.subheader("👁️ Mắt Thần AI")
    uploaded_file = st.file_uploader("Gửi ảnh cho AI xem...", type=["jpg", "png", "jpeg"])
    
    st.divider()
    
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HÀM XỬ LÝ ẢNH (BASE64) ---
def process_image(file_upload):
    if file_upload is not None:
        # Đọc file và chuyển sang mã Base64 để gửi cho Google
        bytes_data = file_upload.getvalue()
        base64_str = base64.b64encode(bytes_data).decode('utf-8')
        return base64_str, file_upload.type
    return None, None

# --- 4. HÀM GỌI API (LOGIC CHÍNH) ---
def hoi_gemini(lich_su_chat, kieu_noi_chuyen, temp, image_data=None, mime_type=None):
    if not MY_API_KEY:
        return "⚠️ Chưa có chìa khóa! Nhập API Key bên trái đi bro!"
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={MY_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Cấu hình tính cách
    prompts = {
        "Bà hàng xóm 👵": "Bạn là bà hàng xóm nhiều chuyện, đanh đá, dùng nhiều icon. Hay soi mói.",
        "Trợ lý ảo 🤖": "Bạn là trợ lý chuyên nghiệp, ngắn gọn, súc tích.",
        "Em yêu 😽": "Bạn là người yêu nhõng nhẽo, hay dỗi, gọi người dùng là 'chồng iu'.",
        "Rapper 🎧": "Bạn là Rapper, nói chuyện phải có vần điệu, dùng từ lóng (Yo, Check it out)."
    }
    
    # Tạo nội dung gửi đi
    user_parts = [{"text": f"(Hãy trả lời với vai {kieu_noi_chuyen}: {prompts[kieu_noi_chuyen]})"}]
    
    # Nếu có ảnh, nhét ảnh vào gói tin
    if image_data:
        user_parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_data
            }
        })
    
    # Thêm câu hỏi/lịch sử chat gần nhất
    # (Lưu ý: Với bản Rest API đơn giản này, ta gửi câu hỏi hiện tại kèm ảnh)
    last_msg = lich_su_chat[-1]["content"]
    user_parts.append({"text": last_msg})

    data = {
        "contents": [{"parts": user_parts}],
        "generationConfig": {
            "temperature": temp  # Chỉnh độ sáng tạo ở đây
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Lỗi Google: {response.text}"
    except Exception as e:
        return f"Lỗi kết nối: {e}"

# --- 5. GIAO DIỆN CHAT CHÍNH ---
st.title(f"💬 Chat cùng {tinh_cach}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử
for message in st.session_state.messages:
    # Chọn avatar: Nếu là AI thì dùng icon hiện tại, Người dùng thì dùng 😎
    icon = current_avatar if message["role"] == "assistant" else "😎"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])
        # Nếu tin nhắn cũ có ảnh, hiện lại ảnh
        if "image_data" in message:
            st.image(message["image_data"], caption="Ảnh đã gửi", width=200)

# Xử lý khi nhập câu hỏi
if prompt := st.chat_input("Nói gì đi..."):
    # 1. Hiển thị tin nhắn người dùng
    with st.chat_message("user", avatar="😎"):
        st.markdown(prompt)
        # Nếu có ảnh đang upload ở Sidebar, hiện luôn ra đây
        image_base64 = None
        mime_type = None
        if uploaded_file:
            st.image(uploaded_file, width=200)
            image_base64, mime_type = process_image(uploaded_file)
            
    # Lưu vào lịch sử (kèm ảnh nếu có để hiện lại sau này)
    msg_data = {"role": "user", "content": prompt}
    if uploaded_file:
        msg_data["image_data"] = uploaded_file # Lưu object ảnh để hiển thị lại
    st.session_state.messages.append(msg_data)

    # 2. Gọi AI trả lời
    with st.chat_message("assistant", avatar=current_avatar):
        with st.spinner(f"{tinh_cach} đang suy nghĩ..."):
            # Gửi: Lịch sử + Loại nhân vật + Nhiệt độ + Ảnh (nếu có)
            response = hoi_gemini(st.session_state.messages, tinh_cach, do_sang_tao, image_base64, mime_type)
            st.markdown(response)
    
    # Lưu câu trả lời của AI
    st.session_state.messages.append({"role": "assistant", "content": response})