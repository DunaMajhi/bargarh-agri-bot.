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

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Activation")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Enter Google API Key", type="password")

# --- MAIN INTERFACE ---
st.title("🌾 Bargarh Krishi Sahayak")
st.markdown("### 👁 Dekhun, Sunun au Bujhun")
st.caption("See, Listen, and Understand")

# --- INPUT SECTION (3 MODES) ---
tab1, tab2, tab3 = st.tabs(["📸 Camera (Photo)", "🎤 Voice (Audio)", "✍ Text (Type)"])

image_input = None
audio_input = None
text_input = None

with tab1:
    st.write("Take a photo of the affected crop:")
    camera_file = st.camera_input("Open Camera")
    if camera_file:
        image_input = Image.open(camera_file)
        st.success("Photo captured!")

with tab2:
    st.write("Tap to Speak (Sambalpuri/Odia):")
    audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹ Stop", key='recorder', format="wav")
    if audio:
        audio_input = audio

with tab3:
    text_input = st.text_area("Type symptoms here:", placeholder="e.g., Patra haldia padu chhe")

# --- LOGIC ENGINE ---
if st.button("🔍 Diagnose"):
    if not api_key:
        st.error("⚠ API Key missing.")
        st.stop()
        
    genai.configure(api_key=api_key)

    # --- 1. SYSTEM INSTRUCTION (The Brain) ---
    sys_instruction = f"""
    Role: Agricultural Expert for Bargarh, Odisha.
    Capabilities: You can analyze Images, Audio (Sambalpuri), and Text.
    
    Database: {json.dumps(knowledge_base)}
    
    Rules:
    1. If an IMAGE is provided, analyze visual symptoms (spots, color, pests).
    2. Map symptoms to the Database.
    3. OUTPUT MUST BE IN ODIA SCRIPT (Sambalpuri Style).
    4. Format:
       - 🛑 Roga (Disease Name)
       - 💊 Aushadh (Medicine Name)
       - 💧 Matra (Dosage)
    """

    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction=sys_instruction
    )

    # --- 2. PREPARE INPUTS ---
    inputs_to_send = []
    
    # We append whatever the user provided. Gemini handles mixed inputs!
    if image_input:
        st.info("👁 Photo dekhuchhe... (Analyzing Photo...)")
        inputs_to_send.append(image_input)
        inputs_to_send.append("Look at this crop. What disease is this based on my database?")
    
    if audio_input:
        st.info("🎧 Sunuchhe... (Listening...)")
        inputs_to_send.append({"mime_type": "audio/wav", "data": audio_input['bytes']})
        
    if text_input:
        inputs_to_send.append(text_input)

    if not inputs_to_send:
        st.warning("⚠ Please provide a Photo, Audio, or Text!")
        st.stop()

    # --- 3. GET RESPONSE ---
    try:
        with st.spinner("🤖 Bhabuchhe... (Thinking...)"):
            response = model.generate_content(inputs_to_send)
            ai_text_odia = response.text
            
            st.markdown(f"### 📢 Uttar (Answer):")
            st.markdown(ai_text_odia)
            
            # Audio Output
            tts = gTTS(text=ai_text_odia, lang='hi')
            sound_file = io.BytesIO()
            tts.write_to_fp(sound_file)
            st.audio(sound_file, format='audio/mp3', start_time=0)
            
    except Exception as e:
        st.error(f"Error: {e}")
