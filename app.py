import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 頁面設定 ---
st.set_page_config(page_title="行事曆分析助理", page_icon="📅")
st.title("📅 智能行事曆分析助理")
st.caption("上傳行事曆截圖或照片，AI 幫您分析行程 | 供內部使用")

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
        {"role": "assistant", "content": "你好！請上傳行事曆照片，我會幫你整理行程。"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- 主要邏輯 ---
if prompt := st.chat_input("輸入指令..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 準備輸入內容
    content_input = [prompt]
    if image:
        content_input.append(image)
        # 加入提示詞引導
        content_input.insert(0, "請分析這張行事曆圖片，列出日期、時間與事件，並檢查衝突。")

    # --- 關鍵修改：模型選擇邏輯 ---
    # 1. 先嘗試用最新的 Flash
    # 2. 失敗則用舊版 Vision
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(content_input) # 嘗試生成
    except Exception as e:
        # 捕捉 404 錯誤，改用舊版模型
        try:
            st.toast("⚠️ 系統提示：切換至 gemini-pro-vision 模型")
            model = genai.GenerativeModel('gemini-pro-vision')
            response = model.generate_content(content_input)
        except Exception as e2:
            st.error(f"所有模型都嘗試失敗。請檢查 API Key 或稍後再試。\n錯誤訊息: {e2}")
            st.stop()

    # 顯示結果
    if response and response.text:
        st.chat_message("assistant").write(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
