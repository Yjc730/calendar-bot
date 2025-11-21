import streamlit as st
import google.generativeai as genai

# --- 頁面設定 ---
st.set_page_config(page_title="行事曆分析助理", page_icon="📅")
st.title("📅 智能行事曆分析助理")
st.caption("由 Google Gemini 驅動 | 免費版")

# --- 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 設定")
    # 讓使用者在介面上輸入 API Key，這樣你不用把 Key 寫死在程式碼裡，比較安全
    api_key = st.text_input("請輸入 Google API Key", type="password")
    st.markdown("[👉 按此免費取得 API Key](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info("💡 說明：請在右側對話框貼上您的行程，AI 會幫您分析時間衝突或給予建議。")

# --- 初始化對話紀錄 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "你好！請貼上你的行程文字（例如：週一 10:00 開會...），我會幫你整理並檢查是否有時間衝突。"}
    ]

# --- 顯示歷史訊息 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 處理使用者輸入 ---
if prompt := st.chat_input("輸入行程安排..."):
    # 檢查有沒有輸入 API Key
    if not api_key:
        st.error("請先在左側欄位輸入 API Key 才能運作喔！")
        st.stop()

    # 顯示使用者輸入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 呼叫 AI
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 系統提示詞：設定 AI 的人設
        system_prompt = """
        你是一位專業的秘書與時間管理專家。請針對使用者的行程文字進行分析：
        1. **整理行程**：列出清晰的時間表。
        2. **偵測衝突**：如果有時間重疊，請務必用粗體警告。
        3. **語氣**：使用繁體中文，親切且專業。
        """
        
        # 組合歷史對話給 AI
        history_for_ai = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                history_for_ai.append({"role": "user", "parts": [msg["content"]]})
            else:
                history_for_ai.append({"role": "model", "parts": [msg["content"]]})
        
        # 發送請求
        with st.chat_message("model"):
            message_placeholder = st.empty()
            # 為了簡化，這裡我們直接把 system prompt 加在最後一次的輸入前
            full_prompt = system_prompt + "\n\n使用者輸入：" + prompt
            
            response = model.generate_content(history_for_ai[:-1] + [{'role':'user', 'parts':[full_prompt]}], stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        st.session_state.messages.append({"role": "model", "content": full_response})

    except Exception as e:
        st.error(f"發生錯誤：{e}。請檢查 API Key 是否正確。")
