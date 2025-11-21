import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 頁面設定 ---
st.set_page_config(page_title="行事曆分析助理", page_icon="📅")
st.title("📅 智能行事曆分析助理")
st.caption("上傳行事曆截圖或照片，AI 幫您分析行程 | 供內部使用")

# --- 自動讀取 API Key (從 Secrets) ---
# 這裡會自動抓取您在 Streamlit 後台設定的 Key，同事不需要輸入
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ 未偵測到 API Key。請管理者至 Streamlit 後台 Settings -> Secrets 設定 GOOGLE_API_KEY。")
    st.stop()

# --- 側邊欄：圖片上傳區 ---
with st.sidebar:
    st.header("📸 上傳行事曆")
    uploaded_file = st.file_uploader("請上傳照片或截圖 (jpg, png)", type=["jpg", "jpeg", "png"])
    
    image_prompt = ""
    if uploaded_file is not None:
        # 顯示預覽圖
        image = Image.open(uploaded_file)
        st.image(image, caption="已上傳的行事曆", use_column_width=True)
        st.success("圖片讀取成功！現在可以在右側對話框要求 AI 分析這張圖。")
    else:
        st.info("💡 提示：您可以截圖 Google Calendar 或拍下紙本行事曆上傳。")

# --- 初始化對話紀錄 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "你好！我是你的行事曆助理。請上傳行事曆照片，或者直接貼上行程文字，我會幫你整理並檢查衝突。"}
    ]

# --- 顯示歷史訊息 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 處理使用者輸入 ---
if prompt := st.chat_input("輸入指令... (例如：幫我分析這週行程有什麼衝突？)"):
    
    # 顯示使用者文字
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 呼叫 AI
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # 準備發送給 AI 的內容
        # 如果有上傳圖片，就把圖片跟文字一起送出去
        if uploaded_file:
            inputs = [prompt, image]
        else:
            inputs = [prompt]

        # 加上系統提示 (System Instruction) 讓 AI 更聰明
        system_prompt = "你是一個專業秘書。請分析使用者的輸入（可能是文字或行事曆圖片）。如果是圖片，請仔細辨識上面的日期與時間。請列出行程清單，並檢查是否有時間衝突。請用繁體中文回答。"
        
        # 這裡我們把系統提示加在 inputs 最前面
        inputs.insert(0, system_prompt)

        with st.chat_message("model"):
            message_placeholder = st.empty()
            
            # 使用 generate_content 處理單次請求（包含圖片）
            # 註：為了簡化圖片處理邏輯，這個版本主要針對當下上傳的圖片進行分析
            response = model.generate_content(inputs, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        st.session_state.messages.append({"role": "model", "content": full_response})

    except Exception as e:
        st.error(f"發生錯誤，請稍後再試：{e}")
