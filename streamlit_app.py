import streamlit as st
import pandas as pd
import os
from PyPDF2 import PdfReader
from docx import Document
from fuzzywuzzy import process

DB_PATH = "Career_Paths_Dataset.xlsx"

def load_database():
    if not os.path.exists(DB_PATH):
        st.error("Database not found! Please upload a dataset in the 'Data Upload' section.")
        return pd.DataFrame()
    try:
        database = pd.read_excel(DB_PATH)
        if database.empty:
            st.warning("The dataset is empty. Please upload a valid dataset.")
            return pd.DataFrame()
        
        required_columns = {"Question", "Response"}
        if not required_columns.issubset(database.columns):
            st.error("Dataset is missing required columns: 'Question' and 'Response'. Please upload a valid dataset.")
            return pd.DataFrame()
        
        return database
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return pd.DataFrame()

def extract_pdf_text(file):
    try:
        reader = PdfReader(file)
        return '\n'.join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_word_text(file):
    try:
        doc = Document(file)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Error reading Word document: {e}")
        return ""

def upload_data():
    uploaded_file = st.file_uploader("Please upload any previous prescription", type=["csv", "xlsx", "pdf", "docx"])
    if uploaded_file:
        try:
            if uploaded_file.type == "text/csv":
                data = pd.read_csv(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                data = pd.read_excel(uploaded_file)
            elif uploaded_file.type == "application/pdf":
                text = extract_pdf_text(uploaded_file)
                st.text_area("Extracted PDF Content", text, height=300)
                return text
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = extract_word_text(uploaded_file)
                st.text_area("Extracted Word Content", text, height=300)
                return text
            else:
                st.error("Unsupported file type!")
                return None
            
            required_columns = {"Question", "Response"}
            if isinstance(data, pd.DataFrame) and not required_columns.issubset(data.columns):
                st.error("Uploaded dataset must contain 'Question' and 'Response' columns.")
                return None
            
            st.dataframe(data)
            data.to_excel(DB_PATH, index=False)  # Save uploaded data
            st.success("Dataset uploaded and saved successfully!")
            return data
        except Exception as e:
            st.error(f"Error processing file: {e}")
    return None

def chatbot(database):
    st.sidebar.header("Chatbot Assistant")
    chatbot_container = st.sidebar.container()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    with chatbot_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        user_input = st.chat_input("Ask something...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            response = get_chatbot_response(user_input, database)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.chat_message("user").markdown(user_input)
            st.chat_message("assistant").markdown(response)

def get_chatbot_response(user_input, database):
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good evening", "namaste"]
    
    if user_input.lower() in greetings:
        return "Hello! How can I assist you today?"
    
    if database.empty or "Question" not in database or "Response" not in database:
        return "I'm here to help, but no valid dataset was found. Please upload a proper dataset."
    
    questions = database["Question"].dropna().tolist()
    if questions:
        best_match, score = process.extractOne(user_input, questions)
        if score > 60:  # Lowered threshold to improve matching
            response = database.loc[database["Question"] == best_match, "Response"].values[0]
            return response
    
    return "I'm here to help, but I couldn't find relevant data. Can you provide more details?"

def main():
    st.title("Career Path Recommender: Career Path Assistance and Comfort Chatbot")
    st.sidebar.header("Navigation")
    options = st.sidebar.radio("Select a page:", ["Home", "Data Upload", "Database", "About"])
    
    database = load_database()
    
    chatbot(database)
    
    if options == "Home":
        st.header("Welcome to the Med Assist Dashboard")
        st.write("This app is designed to provide AI-powered diagnostic assistance and chatbot interactions.")
    
    elif options == "Data Upload":
        st.header("Please upload any previous prescription")
        new_data = upload_data()
        if new_data is not None:
            st.session_state.new_data = new_data
    
    elif options == "Database":
        st.header("Database Overview")
        if database.empty:
            st.warning("Database not found! Please upload a dataset.")
        else:
            st.dataframe(database)
    
    elif options == "About":
        st.header("About This App")
        st.write("Med Assist: AI-Powered Diagnostic Assistance and Comfort Chatbot is an intelligent healthcare chatbot designed to assist users in understanding their symptoms and providing relevant medical insights. The chatbot leverages a structured dataset containing common health-related queries and responses, allowing users to receive instant guidance on symptoms like fever, headache, stress, and more. Additionally, users can upload previous prescriptions in formats like PDF, Word, or Excel to extract useful data for further analysis. With an intuitive interface and AI-driven responses, Med Assist aims to enhance accessibility to basic healthcare information and improve user well-being.")

if __name__ == "__main__":
    main()
