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
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Prepare Input
    inputs_to_send = []
    
    # 1. SYSTEM PROMPT (THE CRITICAL CHANGE)
    # We force the AI to reply in Odia/Sambalpuri Script
    system_prompt = f"""
    Role: Agricultural Expert for Bargarh, Odisha.
    You speak Sambalpuri/Odia.
    
    Database: {json.dumps(knowledge_base)}
    
    Task: 
    1. Analyze the input (Audio or Text).
    2. Identify the disease from the database.
    3. **OUTPUT MUST BE IN ODIA SCRIPT (Sambalpuri Style).** 4. Structure the answer like this:
       - 🛑 Roga (Disease Name)
       - 💊 Aushadh (Medicine Name)
       - 💧 Matra (Dosage)
    5. Keep it simple and direct for a farmer.
    """
    inputs_to_send.append(system_prompt)

    # 2. Add User Content
    if audio:
        st.info("🎧 Sunuchhe... (Listening...)")
        inputs_to_send.append({"mime_type": "audio/wav", "data": audio['bytes']})
    elif user_text:
        st.info("📝 Padhuchhe... (Reading...)")
        inputs_to_send.append(user_text)
    else:
        st.warning("⚠️ Please speak or type something!")
        st.stop()

    # 3. Get Response & Speak It
    try:
        with st.spinner("🤖 Bhabuchhe... (Thinking...)"):
            # A. Generate Text
            response = model.generate_content(inputs_to_send)
            ai_text_odia = response.text
            
            # Display the Text (Odia Script)
            st.markdown(f"### 📢 Uttar (Answer):")
            st.markdown(ai_text_odia)
            
            # B. Generate Audio (Text-to-Speech)
            # We use 'or' (Odia) for the accent
            tts = gTTS(text=ai_text_odia, lang='hi')
            
            # Save to memory (not disk) to play instantly
            sound_file = io.BytesIO()
            tts.write_to_fp(sound_file)
            
            # Show the Audio Player
            st.audio(sound_file, format='audio/mp3', start_time=0)
            
    except Exception as e:
        st.error(f"Error: {e}")
