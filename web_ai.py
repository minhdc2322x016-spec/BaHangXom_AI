import streamlit as st
import requests
import json

# --- CẤU HÌNH ---
# Dán API Key của bạn vào đây
# Lấy key từ két sắt bí mật của Streamlit, không để lộ ra ngoài
MY_API_KEY = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(page_title="Bà Hàng Xóm AI", page_icon="🤬")
st.title("🤬 Bà Hàng Xóm Đanh Đá")
st.caption("Chuyên tư vấn tình cảm, đòi nợ, và vẽ tranh minh họa")

# --- HÀM GỌI API GEMINI (CÓ TRÍ NHỚ) ---
def hoi_gemini(lich_su_chat):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={MY_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Chuẩn bị dữ liệu gửi đi (Đúng chuẩn Google yêu cầu để nhớ lịch sử)
    # Google yêu cầu role là 'user' hoặc 'model' (thay vì 'assistant')
    google_history = []
    for msg in lich_su_chat:
        role_google = "user" if msg["role"] == "user" else "model"
        google_history.append({
            "role": role_google,
            "parts": [{"text": msg["content"]}]
        })
        
    # Thêm chỉ dẫn "Nhân cách" vào đầu câu chuyện để AI không bị quên vai
    nhan_cach = {
        "role": "user",
        "parts": [{"text": "HÃY NHỚ: Bạn là một bà hàng xóm cực kỳ đanh đá, dùng nhiều icon, nói chuyện hài hước. Nếu người dùng yêu cầu vẽ, hãy mô tả bức tranh đó bằng tiếng Anh."}]
    }
    google_history.insert(0, nhan_cach)

    data = { "contents": google_history }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Lỗi Google: {response.text}"
    except Exception as e:
        return f"Lỗi kết nối: {e}"

# --- GIAO DIỆN CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử cũ
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Nếu trong tin nhắn cũ có hình ảnh (được đánh dấu đặc biệt), hiển thị lại
        if "image_url" in message:
            st.image(message["image_url"])

# Xử lý khi nhập câu hỏi mới
if prompt := st.chat_input("Hỏi gì hỏi lẹ đi..."):
    # 1. Hiển thị câu hỏi người dùng
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Xử lý Logic: Vẽ hay Chat?
    if "vẽ" in prompt.lower():
        # --- CHẾ ĐỘ VẼ TRANH ---
        with st.chat_message("assistant"):
            st.markdown("Ok, chờ tí tôi vẽ cho xem! 🎨")
            
            # Bước 1: Nhờ AI viết mô tả tranh bằng tiếng Anh (Vì công cụ vẽ cần tiếng Anh)
            prompt_ve = f"Hãy viết một mô tả ngắn gọn bằng tiếng Anh để vẽ bức tranh về: {prompt.replace('vẽ', '')}"
            
            # Tạo lịch sử giả lập để nhờ AI dịch
            history_temp = st.session_state.messages.copy()
            history_temp.append({"role": "user", "content": prompt_ve})
            
            mo_ta_tieng_anh = hoi_gemini(history_temp)
            
            # Bước 2: Gọi API vẽ tranh (Pollinations AI - Miễn phí)
            # Chúng ta nhúng mô tả vào đường link
            image_url = f"https://image.pollinations.ai/prompt/{mo_ta_tieng_anh}"
            
            st.image(image_url, caption="Tranh minh họa nè!")
            st.markdown(f"*(Mô tả: {mo_ta_tieng_anh})*")
            
            # Lưu vào lịch sử
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Đây là tranh tôi vẽ nè!",
                "image_url": image_url
            })
            
    else:
        # --- CHẾ ĐỘ CHAT BÌNH THƯỜNG ---
        with st.chat_message("assistant"):
            with st.spinner("Đang nghĩ câu khịa..."):
                response = hoi_gemini(st.session_state.messages)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})