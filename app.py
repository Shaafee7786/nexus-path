import streamlit as st
import fitz  # PyMuPDF
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_epub(file):
    with open("temp.epub", "wb") as f:
        f.write(file.getbuffer())
    # Warning suppression for ebooklib
    book = epub.read_epub("temp.epub")
    text = ""
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        text += soup.get_text() + "\n"
    return text

def generate_ai_response(content, language, task_type, api_key):
    llm = ChatOpenAI(model="gpt-4o", openai_api_key=api_key)
    if task_type == "Summary":
        sys_prompt = f"You are an expert educator. Summarize the text in {language} with clear instructions."
    else:
        sys_prompt = f"You are a Life Architect. Create a 30-day life action plan in {language} based on the core principles of these books. Make it actionable for daily life."
    
    # We use the updated import path here
    messages = [
        SystemMessage(content=sys_prompt), 
        HumanMessage(content=f"Here is the content: {content[:15000]}")
    ]
    return llm.invoke(messages).content

# UI Setup
st.set_page_config(page_title="NexusPath", page_icon="📚")
st.title("📚 NexusPath: Book-to-Action")

with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("OpenAI API Key", type="password")
    output_lang = st.selectbox("Language", ["English", "Spanish", "French", "German", "Portuguese", "Italian", "Dutch"])
    st.info("The AI uses GPT-4o to analyze your books and build a roadmap.")

uploaded_files = st.file_uploader("Upload PDF or EPUB books", type=["pdf", "epub"], accept_multiple_files=True)

if uploaded_files:
    combined_text = ""
    for f in uploaded_files:
        if f.type == "application/pdf":
            combined_text += extract_text_from_pdf(f)
        else:
            combined_text += extract_text_from_epub(f)
    
    st.success(f"Loaded {len(uploaded_files)} book(s).")
    
    if st.button("Generate Summary & Action Plan"):
        if not api_key:
            st.error("Please enter your OpenAI API Key in the sidebar.")
        else:
            with st.spinner("Processing your library..."):
                try:
                    res = generate_ai_response(combined_text, output_lang, "Plan", api_key)
                    st.markdown("---")
                    st.markdown(res)
                except Exception as e:
                    st.error(f"An error occurred: {e}")
