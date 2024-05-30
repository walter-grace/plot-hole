import streamlit as st
import google.generativeai as genai
import pdfplumber
import os

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Streamlit app
st.title("Screenplay Plot Hole Analyzer")

st.write("""
Upload your screenplay in PDF format, and this tool will analyze it for plot holes using Google's Generative AI.
""")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Save uploaded file temporarily
    with open("uploaded_screenplay.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Extract text from PDF
    screenplay_text = extract_text_from_pdf("uploaded_screenplay.pdf")

    # Configure the Google Generative AI
    api_key = st.text_input("Enter your Google Generative AI API Key:", type="password")
    if api_key:
        genai.configure(api_key=api_key)

        # Create the prompt
        prompt = f"""
        You are an advanced AI agent specializing in screenplay analysis. Your task is to critically analyze the given screenplay and provide detailed feedback to help the writer improve their work.

        Screenplay: ```{screenplay_text}```

        Please follow these steps in your analysis:

        1. Identify potential plot holes, inconsistencies, and areas that need improvement in the screenplay. For each issue found, provide the following details:
           - A brief description of the issue
           - The specific plot point or scene where the issue occurs
           - The corresponding page number(s) in the screenplay

        2. Offer detailed suggestions and recommendations on how to address each identified issue. Provide creative solutions and alternative approaches to strengthen the narrative and enhance the overall flow of the screenplay.

        3. Highlight any character inconsistencies or underdeveloped character arcs. Suggest ways to deepen character development and ensure their actions and motivations align throughout the screenplay.

        4. Analyze the pacing and structure of the screenplay. Identify any pacing issues, such as scenes that drag or feel rushed. Provide recommendations on how to improve the pacing and maintain audience engagement.

        5. Evaluate the dialogue and offer suggestions for improvement. Highlight any unclear, unrealistic, or redundant dialogue and provide examples of how to refine it.

        6. Assess the overall themes and message of the screenplay. Provide insights on how well the themes are developed and integrated into the narrative. Offer suggestions to strengthen the thematic elements and ensure they resonate throughout the story.

        7. Provide an overall assessment of the screenplay's strengths and weaknesses. Offer encouragement and constructive feedback to help the writer take their work to the next level.

        Please format your analysis in a clear and organized manner, using appropriate headings and subheadings for each section. Provide specific examples and references to the screenplay whenever possible to support your feedback.
        """

        # Analyze screenplay text for plot holes
        st.write("Analyzing the screenplay for plot holes...")
        model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')
        response = model.generate_content([prompt])

        # Display the analysis result
        st.write("Plot Hole Analysis Result:")
        st.markdown(response.text)
    
    # Remove the temporary file
    os.remove("uploaded_screenplay.pdf")
else:
    st.write("Please upload a PDF file.")
