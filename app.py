import streamlit as st
import google.generativeai as genai
import json
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import io
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Chaasi Sahayak", page_icon="🌾", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    with open('diseases.json', 'r') as f:
        return json.load(f)

knowledge_base = load_data()

# --- INIT CHAT HISTORY ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR (SETTINGS) ---
with st.sidebar:
    st.header("⚙ Settings")
    
    # 1. LANGUAGE SELECTOR (THE NEW FEATURE)
    selected_language = st.selectbox(
        "Choose Language / Bhasha:",
        ["Sambalpuri (Odia Script)", "Chhattisgarhi (Devanagari)", "Gondi (Devanagari)", "Bhili (Devanagari)", "Khandeshi (Devanagari)", "Hindi", "English"]
    )
    
    st.divider()
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Enter Google API Key", type="password")
    
    # History Display
    st.subheader("📜 History")
    history_container = st.container(height=300)
    with history_container:
        if not st.session_state.chat_history:
            st.caption("No conversation yet.")
        else:
            for message in st.session_state.chat_history:
                role_icon = "👨‍🌾" if message["role"] == "user" else "🤖"
                with st.chat_message(message["role"], avatar=role_icon):
                    st.markdown(message["content"])

    if st.button("🗑 Clear History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🌾 Chaasi Sahayak")
st.caption(f"AI Doctor speaking *{selected_language}*")

# --- INPUT SECTION ---
tab1, tab2, tab3 = st.tabs(["✍ Text", "🎤 Voice", "📸 Photo"])

user_input = None
image_input = None

with tab1:
    text_val = st.text_input("Type symptoms:", key="txt_input")
    if text_val: user_input = text_val

with tab2:
    st.write("Tap to Speak:")
    audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹ Stop", key='recorder', format="wav")
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

    # Add to History
    history_label = "📸 [Photo]" if image_input else "🎤 [Audio]" if isinstance(user_input, dict) else user_input
    st.session_state.chat_history.append({"role": "user", "content": history_label})

    genai.configure(api_key=api_key)

# --- DYNAMIC SYSTEM INSTRUCTION (WITH EXAMPLES) ---
    target_script = "Odia Script" if "Sambalpuri" in selected_language else "Devanagari Script"
    
    # We teach the AI the difference between Standard vs Dialect
    linguistic_examples = ""
    if "Sambalpuri" in selected_language:
        linguistic_examples = """
        USE SAMBALPURI VOCABULARY, NOT STANDARD ODIA:
        - Don't say: "Kemitii Achhanti" -> Say: "Kenta Acho"
        - Don't say: "Kuha" -> Say: "Kahana"
        - Don't say: "Kouthi" -> Say: "Kene"
        - Use rural words like 'Chasi', 'Bihana', 'Dhan' instead of formal Sanskritized Odia.
        """
    elif "Gondi" in selected_language:
        linguistic_examples = """
        USE GONDI VOCABULARY IN DEVANAGARI:
        - Don't use pure Hindi grammar.
        - Use Gondi sentence structure (SOV).
        - Use words like 'Johar' (Greetings), 'Nawa' (My), 'Id' (This).
        """
    
    sys_instruction = f"""
    Role: Expert Agricultural AI (Chaasi Sahayak) for Central India.
    Current Mode: Speaking *{selected_language}*.
    
    Resources: {json.dumps(knowledge_base)}
    
    LINGUISTIC STYLE GUIDE:
    {linguistic_examples}
    
    STRICT RULES:
    1. *Language:* Translate your reasoning into *{selected_language}*.
    2. *Script:* Write the output using *{target_script}*.
    3. *Tone:* Rustic, simple, rural. Avoid textbook language.
    
    FORMAT:
    ### 🛑 Disease ({selected_language}): ...
    ### 📝 Reason: ...
    ### 💊 Medicine: ...
    """    
    # Safe Mode (No Tools to prevent crash)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instruction)
    chat = model.start_chat(history=[])
    
    inputs_to_send = []
    
    if image_input:
        inputs_to_send.append(image_input)
        inputs_to_send.append(f"Diagnose this crop. Explain in {selected_language}.")
    
    if isinstance(user_input, dict): 
        inputs_to_send.append(user_input)
    elif user_input: 
        inputs_to_send.append(user_input)

# --- 3. GET RESPONSE ---
    with st.spinner("🤖 Bhabuchhe..."):
        try:
            response = chat.send_message(inputs_to_send)
            ai_text = response.text
            
            # Display Result (Keep Emojis for Visuals)
            st.markdown("### 📢 Result:")
            st.markdown(ai_text)
            
            # --- CLEAN TEXT FOR AUDIO (Remove Emojis & Markdown) ---
            def clean_for_audio(text):
                # 1. Remove Markdown
                text = text.replace("*", "").replace("#", "").replace("- ", "")
                
                # 2. Remove Specific Emojis (The ones we use in prompts)
                emojis_to_remove = ["🛑", "📝", "💊", "📢", "🌍", "🔎", "🗣", "🌾", "👁", "🎧"]
                for emoji in emojis_to_remove:
                    text = text.replace(emoji, "")
                
                return text

            speech_text = clean_for_audio(ai_text)
            
            # Generate Audio
            tts = gTTS(text=speech_text, lang='hi')
            sound_file = io.BytesIO()
            tts.write_to_fp(sound_file)
            st.audio(sound_file, format='audio/mp3', start_time=0)

            # Save to History
            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
            
        except Exception as e:
            st.error(f"Error: {e}")
