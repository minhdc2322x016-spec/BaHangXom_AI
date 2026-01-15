import streamlit as st
import requests
import json
import base64
from gtts import gTTS
import io

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="AI Biết Nói", page_icon="🎙️", layout="wide")

# --- 2. CSS & GIAO DIỆN ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stChatInput {position: fixed; bottom: 30px;}
</style>
""", unsafe_allow_html=True)

# --- 3. MENU BÊN TRÁI ---
with st.sidebar:
    st.header("🎛️ Cấu hình")
    
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

    # CHỌN GIỌNG ĐỌC
    st.subheader("🗣️ Cài đặt giọng nói")
    che_do_noi = st.toggle("Bật giọng nói AI", value=True)
    
    st.divider()
    
    # CHỌN NHÂN VẬT
    tinh_cach = st.radio("Chọn vai:", ["Trợ lý ảo 🤖", "Chị Google 🇻🇳", "Bà hàng xóm 👵"])
    
    if st.button("🗑️ Xóa chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. HÀM XỬ LÝ ÂM THANH (TEXT TO SPEECH) ---
def text_to_speech(text):
    try:
        # Tạo file âm thanh từ văn bản (lang='vi' là tiếng Việt)
        tts = gTTS(text=text, lang='vi', slow=False)
        
        # Lưu vào bộ nhớ tạm thay vì lưu ra ổ cứng
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        return None

# --- 5. HÀM GỌI GEMINI ---
def hoi_gemini(lich_su, vai):
    if not MY_API_KEY: return "Chưa có Key bạn ơi!"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={MY_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompts = {
        "Trợ lý ảo 🤖": "Bạn là trợ lý lịch sự, trả lời ngắn gọn.",
        "Chị Google 🇻🇳": "Bạn là chị Google, trả lời giọng đều đều, hài hước.",
        "Bà hàng xóm 👵": "Bạn là bà hàng xóm nhiều chuyện."
    }
    
    full_prompt = [{"role": "user", "parts": [{"text": f"HÃY NHỚ: {prompts[vai]}. " + lich_su[-1]["content"]}]}]
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps({"contents": full_prompt}))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
    except: pass
    return "Lỗi kết nối rồi!"

# --- 6. GIAO DIỆN CHÍNH ---
st.title("🎙️ Chatbot Biết Nói")

if "messages" not in st.session_state: st.session_state.messages = []

# Hiện lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Nếu tin nhắn cũ có âm thanh, hiện lại nút play
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# Xử lý chat
if prompt := st.chat_input("Gõ gì đó đi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Đang trả lời..."):
            reply = hoi_gemini(st.session_state.messages, tinh_cach)
            st.markdown(reply)
            
            # Xử lý giọng nói
            audio_data = None
            if che_do_noi:
                with st.spinner("Đang tạo giọng nói..."):
                    audio_data = text_to_speech(reply)
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3", start_time=0)
    
    # Lưu tin nhắn và file âm thanh vào lịch sử
    msg_data = {"role": "assistant", "content": reply}
    if audio_data: msg_data["audio"] = audio_data
    st.session_state.messages.append(msg_data)