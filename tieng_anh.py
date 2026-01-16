import streamlit as st
import requests
import json
import io
from gtts import gTTS

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="English Tutor AI", page_icon="🎓", layout="wide")

# --- 2. GIAO DIỆN & CSS (ĐÃ NÂNG CẤP) ---
st.markdown("""
<style>
    /* Ẩn Menu mặc định */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- TÙY CHỈNH THANH CHAT --- */
    
    /* 1. Chỉnh khung nhập liệu cao hơn */
    .stChatInput textarea {
        min-height: 100px !important;  /* Tăng chiều cao (Mặc định là khoảng 50px) */
        font-size: 18px !important;    /* Chữ to hơn cho dễ đọc */
        padding-top: 15px !important;  /* Căn chỉnh lề trên cho đẹp */
    }
    
    /* 2. Đẩy khung chat lên cao một chút (tránh bị che bởi taskbar máy tính) */
    .stChatInput {
        padding-bottom: 40px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. THANH MENU BÊN TRÁI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3898/3898082.png", width=100)
    st.header("🎓 English Tutor")
    
    # KẾT NỐI KEY
    MY_API_KEY = None
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
            st.success("✅ Connected")
    except: pass
        
    if not MY_API_KEY:
        MY_API_KEY = st.text_input("API Key:", type="password")
    
    st.divider()

    # CẤU HÌNH HỌC TẬP
    st.subheader("📚 Chế độ học")
    mode_hoc = st.radio(
        "Bạn muốn học gì?",
        ["Sửa Lỗi Ngữ Pháp 📝", "Luyện Giao Tiếp 🗣️", "Trau Dồi Từ Vựng 📖"]
    )
    
    st.divider()
    
    che_do_noi = st.toggle("Luyện nghe (Audio)", value=True)
    
    if st.button("Xóa bài học cũ 🗑️"):
        st.session_state.messages = []
        st.rerun()

# --- 4. HÀM XỬ LÝ GIỌNG NÓI (TIẾNG ANH) ---
def text_to_speech(text):
    try:
        # Chuyển sang lang='en' để đọc tiếng Anh chuẩn
        tts = gTTS(text=text, lang='en', slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except:
        return None

# --- 5. HÀM GỌI GEMINI (ĐÃ CHỈNH SỬA) ---
def hoi_gemini(lich_su, mode):
    if not MY_API_KEY: return "Please enter your API Key first!"
    
    # Dùng model chuẩn đã test thành công
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={MY_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompts = {
        "Sửa Lỗi Ngữ Pháp 📝": """Bạn là giáo viên ngữ pháp. Nhiệm vụ: Kiểm tra lỗi sai, giải thích bằng tiếng Việt, viết lại câu đúng. Nếu đúng rồi thì khen ngợi.""",
        "Luyện Giao Tiếp 🗣️": """Bạn là bạn bản xứ (Native Speaker). Trò chuyện tự nhiên bằng Tiếng Anh, ngắn gọn, dùng từ lóng nhẹ nhàng.""",
        "Trau Dồi Từ Vựng 📖": """Bạn là từ điển. Giải thích nghĩa từ vựng, đưa ra 3 ví dụ, từ đồng nghĩa và trái nghĩa."""
    }
    
    system_instruction = prompts[mode]
    
    # --- XỬ LÝ LỊCH SỬ CHAT ---
    google_history = []
    
    # 1. Chuyển đổi lịch sử
    for msg in lich_su:
        role = "user" if msg["role"] == "user" else "model"
        google_history.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    # 2. GỘP LUẬT CHƠI VÀO CÂU ĐẦU (Tránh lỗi 400)
    if google_history:
        first_msg_content = google_history[0]["parts"][0]["text"]
        google_history[0]["parts"][0]["text"] = f"SYSTEM INSTRUCTION: {system_instruction}\n\nUser says: {first_msg_content}"
    else:
        google_history.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}"}]})

    try:
        response = requests.post(url, headers=headers, data=json.dumps({"contents": google_history}))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error form Google: {response.text}"
    except Exception as e: 
        return f"Connection Error: {e}"
    # --- BÍ KÍP PROMPT ENGINEERING CHO GIÁO DỤC ---
    prompts = {
        "Sửa Lỗi Ngữ Pháp 📝": """
            Bạn là một giáo viên ngữ pháp tiếng Anh khó tính nhưng tận tâm.
            Nhiệm vụ:
            1. Kiểm tra câu tiếng Anh của người dùng.
            2. Nếu có lỗi sai, hãy chỉ ra lỗi đó và giải thích ngắn gọn bằng tiếng Việt.
            3. Viết lại câu đúng hoàn chỉnh.
            4. Nếu câu đã đúng, hãy khen ngợi và gợi ý một cách diễn đạt hay hơn (Advanced).
        """,
        "Luyện Giao Tiếp 🗣️": """
            Bạn là một người bạn bản xứ (Native Speaker) vui tính.
            Nhiệm vụ: 
            1. Trò chuyện tự nhiên với người dùng hoàn toàn bằng Tiếng Anh.
            2. Không sửa lỗi ngữ pháp trừ khi lỗi quá nặng gây hiểu lầm.
            3. Đặt câu hỏi ngược lại để duy trì cuộc hội thoại.
            4. Dùng từ ngữ thông dụng, slang nhẹ nhàng.
        """,
        "Trau Dồi Từ Vựng 📖": """
            Bạn là từ điển sống.
            Nhiệm vụ:
            1. Khi người dùng đưa ra một chủ đề hoặc từ vựng, hãy giải thích nghĩa.
            2. Đưa ra 3 ví dụ (Example sentences) cách dùng từ đó trong thực tế.
            3. Đưa ra các từ đồng nghĩa (Synonyms) và trái nghĩa (Antonyms).
        """
    }
    
    system_instruction = prompts[mode]
    
    # Gói tin gửi đi
    full_history = []
    # Thêm chỉ dẫn hệ thống vào đầu
    full_history.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}"}]})
    
    # Thêm lịch sử chat
    for msg in lich_su:
        role = "user" if msg["role"] == "user" else "model"
        # Bỏ qua phần audio trong lịch sử khi gửi cho Gemini
        full_history.append({"role": role, "parts": [{"text": msg["content"]}]})

    try:
        response = requests.post(url, headers=headers, data=json.dumps({"contents": full_history}))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Error from Google AI."
    except: 
        return "Connection Error."

# --- 6. GIAO DIỆN CHÍNH ---
st.title("🇬🇧 English Tutor AI")
st.caption("Luyện tiếng Anh cùng Gia sư AI 24/7")

if "messages" not in st.session_state: st.session_state.messages = []

# Hiển thị lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# Xử lý nhập liệu
if prompt := st.chat_input("Practice English here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = hoi_gemini(st.session_state.messages, mode_hoc)
            st.markdown(reply)
            
            # Tạo giọng đọc Tiếng Anh
            audio_data = None
            if che_do_noi:
                audio_data = text_to_speech(reply)
                if audio_data:
                    st.audio(audio_data, format="audio/mp3", start_time=0)
    
    msg_data = {"role": "assistant", "content": reply}
    if audio_data: msg_data["audio"] = audio_data
    st.session_state.messages.append(msg_data)
    # ... (Các code cũ trong sidebar giữ nguyên) ...
    
    st.divider() # Kẻ đường gạch ngang ngăn cách
    st.info("👨‍💻 Tác giả: **[Trần Minh]**") 
    st.caption("© 2026 - Bản quyền thuộc về [Trần Minh]")