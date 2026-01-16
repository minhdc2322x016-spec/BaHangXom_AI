import streamlit as st
import requests
import json
import io
from gtts import gTTS

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Bà Hàng Xóm AI", page_icon="👵", layout="wide")

# --- 2. GIAO DIỆN & CSS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stChatInput {position: fixed; bottom: 30px;}
</style>
""", unsafe_allow_html=True)

# --- 3. MENU BÊN TRÁI ---
with st.sidebar:
    st.header("👵 Cấu hình Bà Hàng Xóm")
    
    # KẾT NỐI KEY
    MY_API_KEY = None
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
            st.success("✅ Đã kết nối Key")
    except: pass
        
    if not MY_API_KEY:
        MY_API_KEY = st.text_input("Dán API Key:", type="password")
    
    st.divider()

    # CHỌN TÍNH CÁCH
    tinh_cach = st.radio("Chọn vai:", ["Bà hàng xóm 👵", "Chị Google 🇻🇳", "Trợ lý ảo 🤖"])
    
    # --- THANH CHỈNH ĐỘ LẦY (ĐÃ QUAY TRỞ LẠI) ---
    st.divider()
    st.subheader("🌡️ Độ Lầy Lội")
    do_lay = st.slider("Nghiêm túc <---> Điên rồ", 0.0, 2.0, 1.0, 0.1)
    
    st.divider()
    
    # CHẾ ĐỘ GIỌNG NÓI
    che_do_noi = st.toggle("Bật loa (Voice)", value=True)
    
    if st.button("🗑️ Xóa chat"):
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    st.caption("👨‍💻 Code by: **[Tên Bạn]**")

# --- 4. HÀM XỬ LÝ ÂM THANH ---
def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='vi', slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except: return None

# --- 5. HÀM GỌI GEMINI (ĐÃ SIẾT CHẶT ĐỘ DÀI) ---
def hoi_gemini(lich_su, vai, nhiet_do):
    if not MY_API_KEY: return "Nhập Key đi đã cháu ơi!"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={MY_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # --- PROMPT MỚI: BẮT BUỘC TRẢ LỜI NGẮN ---
    prompts = {
        "Bà hàng xóm 👵": """
            Bạn là bà hàng xóm nhiều chuyện, đanh đá, giọng điệu chợ búa.
            QUY TẮC TỐI MẬT:
            1. Trả lời CỰC NGẮN (tối đa 2 câu).
            2. Không giải thích dài dòng, đi thẳng vào vấn đề.
            3. Dùng từ ngữ đời thường (Gớm, ối dồi ôi, cái con này).
        """,
        "Chị Google 🇻🇳": """
            Bạn là Chị Google. Trả lời ngắn gọn, hài hước, giọng đều đều như robot. Tối đa 30 từ.
        """,
        "Trợ lý ảo 🤖": """
            Bạn là trợ lý AI chuyên nghiệp. Trả lời ngắn gọn, súc tích, đi thẳng vào trọng tâm.
        """
    }
    
    system_instruction = prompts[vai]
    
    # Xử lý lịch sử chat
    google_history = []
    
    # Gộp Prompt vào tin nhắn đầu tiên để Google luôn nhớ
    user_msg_content = lich_su[-1]["content"]
    full_prompt = f"HÃY NHỚ: {system_instruction}\n\nNgười dùng hỏi: {user_msg_content}"
    
    # Chỉ gửi tin nhắn cuối cùng kèm chỉ dẫn (để tiết kiệm token và tránh loạn)
    # Hoặc gửi cả lịch sử nhưng phải đảm bảo format
    google_history.append({"role": "user", "parts": [{"text": full_prompt}]})

    data = {
        "contents": google_history,
        "generationConfig": {
            "temperature": nhiet_do, # Chỉnh độ lầy ở đây
            "maxOutputTokens": 100   # GIỚI HẠN SỐ CHỮ TRẢ LỜI (Cho bả bớt nói nhiều)
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Mạng mẽo chán quá, bà không nghe rõ!"
    except: return "Lỗi kết nối rồi!"

# --- 6. GIAO DIỆN CHÍNH ---
st.title(f"💬 Chat cùng {tinh_cach}")

if "messages" not in st.session_state: st.session_state.messages = []

# Hiện lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# Xử lý chat
if prompt := st.chat_input("Nói xấu ai đó đi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Bà đang nghĩ..."):
            # Truyền thêm biến do_lay (nhiệt độ) vào hàm
            reply = hoi_gemini(st.session_state.messages, tinh_cach, do_lay)
            st.markdown(reply)
            
            audio_data = None
            if che_do_noi:
                audio_data = text_to_speech(reply)
                if audio_data:
                    st.audio(audio_data, format="audio/mp3", start_time=0)
    
    msg_data = {"role": "assistant", "content": reply}
    if audio_data: msg_data["audio"] = audio_data
    st.session_state.messages.append(msg_data)
    
    st.divider() # Kẻ đường gạch ngang ngăn cách
    st.info("👨‍💻 Tác giả: **[Trần Minh]**") 
    st.caption("© 2026 - Bản quyền thuộc về [Trần Minh]")