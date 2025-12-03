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
        # Load your local "Textbook"
        return json.load(f)

knowledge_base = load_data()

# --- INIT CHAT HISTORY ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR (HISTORY & KEYS) ---
with st.sidebar:
    st.header("🔑 Activation")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Enter Google API Key", type="password")
    
    st.divider()
    
    # --- HISTORY SECTION ---
    st.subheader("📜 Purana Katha (History)")
    history_container = st.container(height=400)
    with history_container:
        if not st.session_state.chat_history:
            st.caption("No conversation yet.")
        else:
            for message in st.session_state.chat_history:
                role_icon = "👨‍🌾" if message["role"] == "user" else "🤖"
                with st.chat_message(message["role"], avatar=role_icon):
                    st.markdown(message["content"])

    st.divider()
    if st.button("🗑 Clear History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🌾 Chaasi Sahayak")
st.caption("AI Doctor with Research Access (Google Search & Papers)")

# --- INPUT SECTION (Tabs) ---
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

    # Add User Input to History
    history_label = "📸 [Sent Photo]" if image_input else "🎤 [Sent Audio]" if isinstance(user_input, dict) else user_input
    st.session_state.chat_history.append({"role": "user", "content": history_label})

    genai.configure(api_key=api_key)

    # --- 1. THE SUPER-DOCTOR BRAIN ---
    sys_instruction = f"""
    Role: Expert Agricultural AI (Chaasi Sahayak) for Bargarh.
    
    YOUR RESOURCES:
    1. *Primary:* Local Knowledge Base (JSON): {json.dumps(knowledge_base)}
    2. *Secondary:* GOOGLE SEARCH (Use this for new diseases, research papers, or weather).
    
    STRICT RULES:
    1. *Language:* ALWAYS reply in *ODIA SCRIPT (Sambalpuri)*. Translate any search results into simple Sambalpuri.
    2. *Research Mode:* If the user asks about a disease NOT in your JSON, or asks for "Latest Research" or "YouTube Video", USE GOOGLE SEARCH.
    3. *Video Links:* If you find a solution via Search, try to provide a YouTube link if available.
    
    DIAGNOSIS FORMAT:
    ### 🛑 ରୋଗ (Disease): ...
    ### 📝 କାରଣ (Reason): ...
    ### 💊 ଔଷଧ (Medicine): ...
    ### 🌍 Research/Video Note: [If you used Search, mention the source/link here in simple Odia]
    """
    
    # --- 2. MODEL INITIALIZATION (THE BULLETPROOF FIX) ---
    # We create the Tool object directly using protos to avoid dictionary parsing errors
    tools = [
        genai.protos.Tool(
            google_search=genai.protos.GoogleSearch()
        )
    ]

    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction=sys_instruction,
        tools=tools 
    )
    
    # Start Chat (Automatic Function Calling is enabled by default with tools)
    chat = model.start_chat(history=[])
    
    inputs_to_send = []
    
    if image_input:
        inputs_to_send.append(image_input)
        inputs_to_send.append("Diagnose this crop. If unsure, search Google for visual matches.")
    
    if isinstance(user_input, dict): 
        inputs_to_send.append(user_input)
    elif user_input: 
        inputs_to_send.append(user_input)

    # --- 3. GET RESPONSE ---
    with st.spinner("🤖 Bhabuchhe... (Checking Database & Internet...)"):
        try:
            response = chat.send_message(inputs_to_send)
            ai_text = response.text
            
            # Display Result
            st.markdown("### 📢 Result:")
            st.markdown(ai_text)
            
            # Show "Grounding Source" if available (The Search Proof)
            try:
                # Check if search was actually used
                if response.candidates[0].grounding_metadata.search_entry_point:
                     st.caption("🔎 Internet Sources Used (Verified via Google Search)")
            except:
                pass

            # Clean Text for Audio
            clean_text = ai_text.replace("*", "").replace("#", "").replace("http", "")
            tts = gTTS(text=clean_text, lang='hi')
            sound_file = io.BytesIO()
            tts.write_to_fp(sound_file)
            st.audio(sound_file, format='audio/mp3', start_time=0)

            # Save to History
            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
            
        except Exception as e:
            st.error(f"Error: {e}")
