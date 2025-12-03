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
st.title("🌾 Chasi Sahayak")
#st.markdown("###  Dekhun, Sunun au Bujhun")
st.caption("See, Listen, and Understand")

# --- INPUT SECTION (3 MODES) ---
tab1, tab2, tab3 = st.tabs(["✍ Text (Type)", "🎤 Voice (Audio)", "📸 Photo (Camera/Upload)"])

text_input = None
audio_input = None
image_input = None


with tab1:
    text_input = st.text_area("Type symptoms here:", placeholder="e.g., Patra haldia padu chhe")

with tab2:
    st.write("Tap to Speak (Sambalpuri/Odia):")
    audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹ Stop", key='recorder', format="wav")
    if audio:
        audio_input = audio


with tab3:
    st.write("### Option 1: Take a Photo")
    camera_file = st.camera_input("Open Camera")
    
    st.write("### Option 2: Upload from Gallery")
    upload_file = st.file_uploader("Choose an image...", type=['jpg', 'jpeg', 'png'])

    # Logic: Prioritize Camera, then Upload
    if camera_file:
        image_input = Image.open(camera_file)
        st.success("📸 Photo captured from Camera!")
    elif upload_file:
        image_input = Image.open(upload_file)
        st.success("📂 Photo loaded from Gallery!")


# --- LOGIC ENGINE ---
if st.button("🔍 Diagnose"):
    if not api_key:
        st.error("⚠ API Key missing.")
        st.stop()
        
    genai.configure(api_key=api_key)

    # --- 1. SYSTEM INSTRUCTION (STRICT MODE) ---
    sys_instruction = f"""
    Role: You are an expert Agricultural AI for Bargarh, Odisha.
    Knowledge Base: {json.dumps(knowledge_base)}
    
    CRITICAL INSTRUCTION - LANGUAGE:
    1. You MUST reply in ODIA SCRIPT (Sambalpuri style).
    2. DO NOT reply in Hindi, Bengali, or English text.
    3. Even if the user speaks English, you reply in Odia Script.
    
    CRITICAL INSTRUCTION - LOGIC:
    1. Look for keywords in the user's input (audio/text) that match the 'symptoms_keywords' in the Knowledge Base.
    2. Even partial matches (e.g., "Nali" -> "Marua Rog") are okay.
    3. If the user says a local term like "Gendi" or "Matiagundhi", map it immediately.
    
    OUTPUT FORMAT (Strictly maintain this):
    
    ### 🛑 ରୋଗ (Disease):
    [Name in Odia] ([Local Name])
    
    ### 📝 କାରଣ (Reason):
    [One line explanation in Odia]
    
    ### 💊 ଔଷଧ (Medicine):
    * *Chemical:* [Chemical Name in English/Odia]
    * *Brand:* [Brand Name]
    * *Matra:* [Dosage in Odia]
    """
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction=sys_instruction
    )

    # --- 2. PREPARE INPUTS ---
    inputs_to_send = []
    
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
