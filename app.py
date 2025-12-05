import streamlit as st
import google.generativeai as genai
import json
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import io
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Chaasi Sahayak", page_icon="🌾", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    try:
        with open('diseases.json', 'r') as f:
            return json.load(f)
    except:
        return []

knowledge_base = load_data()

# --- INIT CHAT HISTORY ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/628/628283.png", width=50)
    st.title("Settings")
    
    selected_language = st.selectbox(
        "🗣 Bhasha (Language):",
        ["Sambalpuri (Odia Script)", "Chhattisgarhi (Devanagari)", "Gondi (Devanagari)", "Bhili (Devanagari)", "Hindi", "English"]
    )
    
    st.divider()
    
    use_internet = st.toggle("🌍 Google Search", value=False)
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Enter Google API Key", type="password")
    
    st.subheader("📜 History")
    with st.container(height=300):
        for message in st.session_state.chat_history:
            role_icon = "👨‍🌾" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=role_icon):
                st.markdown(message["content"])

    if st.button("🗑 Clear"):
        st.session_state.chat_history = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🌾 Chaasi Sahayak")
st.caption(f"AI Doctor speaking *{selected_language}*")

# --- INPUTS ---
tab1, tab2, tab3 = st.tabs(["✍ Text", "🎤 Voice", "📸 Photo"])

user_input = None
image_input = None

with tab1:
    text_val = st.text_input("Type symptoms:", key="txt_input")
    if text_val: user_input = text_val

with tab2:
    st.write("Tap to Speak:")
    audio = mic_recorder(start_prompt="🎤 Start", stop_prompt="⏹ Stop", key='recorder', format="wav")
    if audio:
        user_input = {"mime_type": "audio/wav", "data": audio['bytes']}

with tab3:
    col_cam, col_up = st.columns(2)
    with col_cam:
        cam = st.camera_input("Camera")
    with col_up:
        up = st.file_uploader("Upload", type=['jpg','png'])
    if cam: image_input = Image.open(cam)
    elif up: image_input = Image.open(up)

# --- LOGIC ENGINE ---
if st.button("🔍 Diagnose / Send", type="primary"):
    if not api_key:
        st.error("⚠ API Key missing.")
        st.stop()
        
    if not user_input and not image_input:
        st.warning("⚠ Please provide input!")
        st.stop()

    # Save to history
    st.session_state.chat_history.append({"role": "user", "content": "📸 [Image]" if image_input else "🎤 [Audio]" if isinstance(user_input, dict) else user_input})

    genai.configure(api_key=api_key)

    target_script = "Odia Script" if "Sambalpuri" in selected_language else "Devanagari Script"
    
    sys_instruction = f"""
    Role: Expert Agricultural AI (Chaasi Sahayak).
    Mode: Speaking {selected_language}.
    Resources: {json.dumps(knowledge_base)}
    
    RULES:
    1. Translate output to {selected_language} using {target_script}.
    2. Tone: Simple, rural, 'Village Elder'.
    3. FORMAT:
       ### 🛑 Disease ({selected_language}): ...
       ### 📝 Reason: ...
       ### 💊 Medicine: ...
    """
    
    # --- FAIL-SAFE MODEL LOADING ---
    model = None
    
    # 1. Try to load with Search Tools
    if use_internet:
        try:
            # We use the dictionary syntax which is safer for Streamlit
            tools = [{"google_search": {}}]
            model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instruction, tools=tools)
        except Exception:
            # If server crashes, silently fallback to normal mode
            model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instruction)
            st.toast("⚠ Search unavailable. Using Offline Mode.", icon="📡")
    else:
        # Normal mode
        model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instruction)

    # --- EXECUTION ---
    chat = model.start_chat(history=[])
    
    inputs_to_send = []
    if image_input:
        inputs_to_send.append(image_input)
        inputs_to_send.append(f"Diagnose this crop. Explain in {selected_language}.")
    if isinstance(user_input, dict): 
        inputs_to_send.append(user_input)
    elif user_input: 
        inputs_to_send.append(user_input)

    with st.spinner("🤖 Bhabuchhe..."):
        try:
            response = chat.send_message(inputs_to_send)
            ai_text = response.text
            
            st.success("✅ Diagnosis Complete!")
            st.markdown(f"### 📢 Result:")
            st.markdown(ai_text)
            
            # Audio
            def clean_for_audio(text):
                text = text.replace("*", "").replace("#", "").replace("- ", "")
                emojis = ["🛑", "📝", "💊", "📢", "🌍", "🔎", "🗣", "🌾", "👁", "🎧", "✅"]
                for e in emojis: text = text.replace(e, "")
                return text

            speech_text = clean_for_audio(ai_text)
            tts = gTTS(text=speech_text, lang='hi')
            sound_file = io.BytesIO()
            tts.write_to_fp(sound_file)
            st.audio(sound_file, format='audio/mp3', start_time=0)

            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
            
        except Exception as e:
            st.error(f"Error: {e}")
