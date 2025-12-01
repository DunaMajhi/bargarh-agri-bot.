import streamlit as st
import google.generativeai as genai
import json

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Bargarh Agri-Bot", page_icon="🌾")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    with open('diseases.json', 'r') as f:
        return json.load(f)

knowledge_base = load_data()

# --- SIDEBAR (SECURE API KEY INPUT) ---
with st.sidebar:
    st.header("🔑 Activation")
    # This checks if the key is in Streamlit Secrets (Cloud) OR lets you type it (Local)
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Enter Google API Key", type="password")
        st.info("Get your key from Google AI Studio")

# --- MAIN INTERFACE ---
st.title("🌾 Bargarh Krishi Sahayak")
user_query = st.text_area("Describe the problem:", placeholder="Example: Grains are empty and smell bad")

if st.button("🔍 Diagnose"):
    if not api_key:
        st.error("⚠ Please enter your API Key in the sidebar!")
    else:
        try:
            genai.configure(api_key=api_key)
            # Using the model you specified
            model = genai.GenerativeModel('gemini-2.0-flash')

            with st.spinner("🤖 AI Doctor is thinking..."):
                prompt = f"""
                Role: Bargarh Agri Expert. 
                Database: {json.dumps(knowledge_base)}
                User Input: "{user_query}"

                Task: Match input to database and prescribe medicine.
                Output: Markdown Format.
                """

                response = model.generate_content(prompt)
                st.markdown(response.text)

        except Exception as e:
            st.error(f"Error: {e}")
