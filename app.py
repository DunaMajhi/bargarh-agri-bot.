import streamlit as st
import google.generativeai as genai
import json
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import io
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Chaasi Sahayak", page_icon="🌾")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    with open('diseases.json', 'r') as f:
        return json.load(f)

knowledge_base = load_data()

# --- INIT CHAT HISTORY ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Activation")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Enter Google API Key", type="password")
    
    # Clear History Button
    if st.button("🗑 Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🌾 Chaasi Sahayak")
st.caption("See, Listen, and Understand")

# --- DISPLAY CHAT HISTORY ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INPUT SECTION ---
# We use a container to keep inputs stable
with st.container():
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
        cam = st.camera_input("Camera")
        up = st.file_uploader("Upload", type=['jpg','png'])
        if cam: image_input = Image.open(cam)
        elif up: image_input = Image.open(up)

# --- LOGIC ENGINE ---
if st.button("🔍 Diagnose / Send"):
    if not api_key:
        st.error("⚠ API Key missing.")
        st.stop()
        
    if not user_input and not image_input:
        st.warning("⚠ Please provide input!")
        st.stop()

    # Add User Input to History (Visual only for now)
    st.session_state.chat_history.append({"role": "user", "content": "Analyze this input..."})

    genai.configure(api_key=api_key)

    # --- 1. SYSTEM INSTRUCTION (STRICT MODE) ---
    sys_instruction = f"""
    Role: Expert Agricultural AI (Chaasi Sahayak) for Bargarh.
    Knowledge Base: {json.dumps(knowledge_base)}
    
    RULES:
    1. Reply in ODIA SCRIPT (Sambalpuri).
    2. Use the Chat History to understand context.
    3. If user asks "What is the price?", assume they mean the medicine from the previous turn.
    4. DIAGNOSIS FORMAT:
       ### 🛑 ରୋଗ (Disease): ...
       ### 💊 ଔଷଧ (Medicine): ...
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instruction)
    
    # --- 2. BUILD CONVERSATION (The Memory Trick) ---
    chat = model.start_chat(history=[])
    
    # Send Inputs
    inputs_to_send = []
    
    # Add previous context summary if needed (Simple version: just send current input)
    # Gemini handles short term context in 'start_chat' usually, but here we are stateless between reruns
    # So we send the current input fresh.
    
    if image_input:
        inputs_to_send.append(image_input)
        inputs_to_send.append("Look at this crop.")
    
    if isinstance(user_input, dict): # Audio
        inputs_to_send.append(user_input)
    elif user_input: # Text
        inputs_to_send.append(user_input)

    # --- 3. GET RESPONSE ---
    with st.spinner("🤖 Bhabuchhe..."):
        try:
            response = chat.send_message(inputs_to_send)
            ai_text = response.text
            
            # Save AI Response to History
            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
            
            # Force Rerun to show new chat
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {e}")
