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
    # Setup Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are a professional Life Architect and Master Educator. 
    Using the provided book text, generate a response in {language}.
    
    1. INSTRUCTIVE SUMMARY: Summarize the core philosophy and the 'Big Ideas'.
    2. LIFE ACTION PLAN: Provide a specific, step-by-step 30-day plan to implement the book's teachings into daily life.
    3. DAILY HABITS: Suggest 3 small habits to start today.

    Text to analyze:
    {content[:50000]} 
    """
    
    response = model.generate_content(prompt)
    return response.text

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
