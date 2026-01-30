import streamlit as st
import fitz  # PyMuPDF
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- EXTRACTION FUNCTIONS ---

def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_epub(file):
    with open("temp.epub", "wb") as f:
        f.write(file.getbuffer())
    # Silence ebooklib warnings
    book = epub.read_epub("temp.epub")
    text = ""
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        text += soup.get_text() + "\n"
    return text

# --- GEMINI AI LOGIC ---

def generate_gemini_response(content, language, api_key):
    genai.configure(api_key=api_key)
    
    # --- AUTO-DETECT AVAILABLE MODELS ---
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as e:
        return f"API Key Error: Could not list models. Check if your key is correct. (Error: {e})"

    if not available_models:
        return "No compatible models found for this API key."

    # --- PICK THE BEST MODEL ---
    # We look for 1.5-flash first, then 1.5-pro, then 1.0-pro
    selected_model = None
    priority = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
    
    for p in priority:
        if p in available_models:
            selected_model = p
            break
    
    if not selected_model:
        selected_model = available_models[0] # Just use whatever is available

    # --- RUN THE ANALYSIS ---
    try:
        model = genai.GenerativeModel(selected_model)
        prompt = f"""
        You are a Life Architect. Based on the following text, 
        generate a summary and a 30-day life action plan in {language}:
        
        {content[:40000]}
        """
        response = model.generate_content(prompt)
        return f"(Using model: {selected_model})\n\n{response.text}"
    except Exception as e:
        return f"Failed to generate content with {selected_model}. Error: {e}"

# --- UI SETUP ---

st.set_page_config(page_title="NexusPath Gemini", page_icon="🚀")
st.title("🚀 NexusPath: Free Book-to-Action")
st.markdown("Extract insights and life plans from your books using Google Gemini.")

with st.sidebar:
    st.header("1. API Setup")
    st.markdown("[Get a Free Gemini Key Here](https://aistudio.google.com/app/apikey)")
    gemini_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.header("2. Preferences")
    output_lang = st.selectbox("Language", ["English", "Spanish", "French", "German", "Portuguese", "Italian"])
    
    st.divider()
    st.info("Gemini 1.5 Flash is free and supports very long books.")

# File uploader
uploaded_files = st.file_uploader("Upload PDF or EPUB", type=["pdf", "epub"], accept_multiple_files=True)

# Processing logic
if uploaded_files:
    combined_text = ""
    for f in uploaded_files:
        if f.type == "application/pdf":
            combined_text += extract_text_from_pdf(f)
        else:
            combined_text += extract_text_from_epub(f)
    
    st.success(f"Successfully read {len(uploaded_files)} book(s).")
    
    if st.button("Build My Life Plan"):
        if not gemini_key:
            st.error("Please paste your Google Gemini Key in the sidebar!")
        else:
            with st.spinner("Gemini is reading your books..."):
                try:
                    # Limit content to roughly 50k characters to stay within free limits easily
                    result = generate_gemini_response(combined_text, output_lang, gemini_key)
                    st.markdown("---")
                    st.markdown(result)
                    st.download_button("Download Plan", result, file_name="my_action_plan.txt")
                except Exception as e:
                    st.error(f"Error: {e}")
else:
    st.info("Upload a book to get started.")
