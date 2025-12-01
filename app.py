import streamlit as st
import google.generativeai as genai
import json
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Bargarh Krishi Sahayak", page_icon="🌾")

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
st.markdown("### 🗣️ Sunun au Samjhun (Listen & Understand)")

# --- AUDIO INPUT ---
col1, col2 = st.columns([1, 4])
with col1:
    st.write("**Tap to Speak:**")
    audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹ Stop", key='recorder', format="wav")

user_text = st.text_area("Or type here:", placeholder="e.g., Matiagundhi lagiche")

# --- LOGIC ENGINE ---
if st.button("🔍 Diagnose"):
    if not api_key:
        st.error("⚠️ API Key missing.")
        st.stop()
        
    genai.configure(api_key=api_key)

    # --- 1. SYSTEM INSTRUCTION (The New, Smarter Way) ---
    # We define the personality here, separate from the user input.
    sys_instruction = f"""
    Role: Agricultural Expert for Bargarh, Odisha.
    You understand Sambalpuri/Odia audio and text.
    
    Database: {json.dumps(knowledge_base)}
    
    Rules:
    1. If input is Sambalpuri, translate internally.
    2. OUTPUT MUST BE IN ODIA SCRIPT (Sambalpuri Style).
    3. Format the answer:
       - 🛑 Roga (Disease Name)
       - 💊 Aushadh (Medicine Name)
       - 💧 Matra (Dosage)
    4. Keep it simple and direct.
    """

    # Initialize the model with the instruction locked in
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction=sys_instruction
    )

    # --- 2. PREPARE USER INPUT ---
    inputs_to_send = []
    
    if audio:
        st.info("🎧 Sunuchhe... (Listening...)")
        inputs_to_send.append({"mime_type": "audio/wav", "data": audio['bytes']})
    elif user_text:
        st.info("📝 Padhuchhe... (Reading...)")
        inputs_to_send.append(user_text)
    else:
        st.warning("⚠️ Please speak or type something!")
        st.stop()

    # --- 3. GET RESPONSE ---
    try:
        with st.spinner("🤖 Bhabuchhe... (Thinking...)"):
            response = model.generate_content(inputs_to_send)
            ai_text_odia = response.text
            
            # Display Text
            st.markdown(f"### 📢 Uttar (Answer):")
            st.markdown(ai_text_odia)
            
            # Generate Audio (Using Hindi engine for Indian accent)
            tts = gTTS(text=ai_text_odia, lang='hi')
            sound_file = io.BytesIO()
            tts.write_to_fp(sound_file)
            st.audio(sound_file, format='audio/mp3', start_time=0)
            
    except Exception as e:
        st.error(f"Error: {e}")
