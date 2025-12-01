import streamlit as st
import google.generativeai as genai
import json
from streamlit_mic_recorder import mic_recorder
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Bargarh Krishi Sahayak", page_icon="🌾")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    with open('diseases.json', 'r') as f:
        return json.load(f)

knowledge_base = load_data()

# --- SIDEBAR (SECURE API KEY) ---
with st.sidebar:
    st.header("🔑 Activation")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Enter Google API Key", type="password")

# --- MAIN INTERFACE ---
st.title("🌾 Bargarh Krishi Sahayak")
st.markdown("### 🎙️ Bolun, Lekhun Nai (Speak, Don't Type)")

# --- AUDIO INPUT SECTION ---
col1, col2 = st.columns([1, 4])
with col1:
    st.write(" **Tap to Speak:**")
    # This creates the microphone button
    audio = mic_recorder(
        start_prompt="🎤 Record",
        stop_prompt="Eq Stop",
        key='recorder',
        format="wav"  # Gemini likes WAV/MP3
    )

user_text = st.text_area("Or type here:", placeholder="e.g., Matiagundhi attack")

# --- LOGIC ENGINE ---
if st.button("🔍 Diagnose"):
    if not api_key:
        st.error("⚠️ API Key missing.")
        st.stop()
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Determine what to send (Audio or Text?)
    inputs_to_send = []
    
    # 1. System Prompt (The Brain)
    system_prompt = f"""
    Role: Agricultural Expert for Bargarh, Odisha.
    You understand Sambalpuri/Odia audio and text.
    
    Database: {json.dumps(knowledge_base)}
    
    Task: 
    1. Listen to the audio OR read the text.
    2. If audio is Sambalpuri, translate it internally.
    3. Match symptoms to the Database.
    4. Output the Diagnosis in Markdown.
    """
    inputs_to_send.append(system_prompt)

    # 2. Add User Content
    if audio:
        st.info("🎧 Analyzing Audio...")
        # Convert raw bytes to a format Gemini accepts
        audio_bytes = audio['bytes']
        inputs_to_send.append({
            "mime_type": "audio/wav",
            "data": audio_bytes
        })
    elif user_text:
        st.info("📝 Analyzing Text...")
        inputs_to_send.append(user_text)
    else:
        st.warning("⚠️ Please speak or type something first!")
        st.stop()

    # 3. Get Response
    try:
        with st.spinner("🤖 AI Doctor is thinking..."):
            response = model.generate_content(inputs_to_send)
            st.markdown(response.text)
    except Exception as e:
        st.error(f"Error: {e}")
