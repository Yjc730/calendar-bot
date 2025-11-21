import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 頁面設定 ---
st.set_page_config(page_title="行事曆分析助理", page_icon="📅")
st.title("📅 智能行事曆分析助理")

# --- 診斷訊息 (除錯用) ---
# 這行會顯示在網頁最上方，確認 SDK 版本是否正確
st.caption(f"系統診斷：Google GenAI SDK 版本: {genai.__version__}")

if genai.__version__ < "0.7.0":
    st.error("⚠️ 系統偵測到版本過舊！請修改 requirements.txt 為 google-generativeai==0.8.3 並選擇 'Reboot app'。")
    st.stop()

# --- 自動讀取 API Key ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ 未偵測到 API Key。請至 Streamlit Settings -> Secrets 設定。")
    st.stop()

# --- 側邊欄 ---
with st.sidebar:
    st.header("📸 上傳行事曆")
    uploaded_file = st.file_uploader("請上傳照片 (jpg, png)", type=["jpg", "jpeg", "png"])
    
    image = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="預覽", use_column_width=True)
        st.success("圖片讀取成功！")

# --- 初始化對話 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是行事曆助理 (使用 Gemini 1.5 Flash 模型)。請上傳照片或輸入文字。"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- 主要邏輯 ---
if prompt := st.chat_input("輸入指令..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 準備輸入
    content_input = [prompt]
    if image:
        content_input.append(image)
        content_input.insert(0, "請分析這張行事曆圖片，列出日期、時間與事件。")

    # 呼叫 AI
    try:
        # 只使用最新的 1.5 Flash，不再退回舊版
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.chat_message("assistant"):
            response = model.generate_content(content_input, stream=True)
            full_response = ""
            placeholder = st.empty()
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"發生錯誤：{e}")
        st.info("如果持續報錯 404，請檢查您的 API Key 是否正確，或該 Key 是否有啟用 Generative AI API 權限。")
