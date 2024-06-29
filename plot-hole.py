import streamlit as st
from solathon import Client, Keypair, PublicKey
from solathon.solana_pay import encode_url, create_qr, find_reference, validate_transfer
from solathon.core.types import TransactionSignature
from io import BytesIO
import time
import pdfplumber
import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
from solathon import Keypair
import tempfile

# Load environment variables
load_dotenv()

# Solana Pay configuration
MERCHANT_WALLET = PublicKey("4EAs5aihFPbxJ3FHXHxKJV6Zic9CM45VhvcRLMFuYTK2")
CUSTOMER_WALLET_PRIVATE_KEY = os.getenv('CUSTOMER_WALLET_PRIVATE_KEY')

# Debug: Print the value of CUSTOMER_WALLET_PRIVATE_KEY
print(f"CUSTOMER_WALLET_PRIVATE_KEY: {CUSTOMER_WALLET_PRIVATE_KEY}")

if CUSTOMER_WALLET_PRIVATE_KEY is None:
    st.error("CUSTOMER_WALLET_PRIVATE_KEY is not set in the environment variables.")
    st.stop()

try:
    CUSTOMER_WALLET = Keypair.from_private_key(bytes.fromhex(CUSTOMER_WALLET_PRIVATE_KEY))
except ValueError as e:
    st.error(f"Error creating CUSTOMER_WALLET: {str(e)}")
    st.error("Make sure CUSTOMER_WALLET_PRIVATE_KEY is a valid hexadecimal string.")
    st.stop()

# Initialize Solana client with mainnet-beta API
client = Client("https://api.mainnet-beta.solana.com")

# Get Google API key from environment variable
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

def checkout_params(amount):
    label = "Screenplay Analysis Service"
    message = "Screenplay Analysis - Order #" + str(int(time.time()))
    reference = Keypair().public_key
    return [label, message, amount, reference]

def generate_payment_link(amount):
    [label, message, amount, reference] = checkout_params(amount)
    url = encode_url({
        "recipient": MERCHANT_WALLET,
        "label": label,
        "message": message,
        "amount": amount,
        "reference": reference
    })
    return url, reference

def create_smaller_qr(url, size=(400, 400)):
    qr_image_stream = create_qr(url)
    qr_image = Image.open(qr_image_stream)
    qr_image_resized = qr_image.resize(size, Image.LANCZOS)
    buffered = BytesIO()
    qr_image_resized.save(buffered, format="PNG")
    return buffered

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def analyze_screenplay(screenplay_text):
    genai.configure(api_key=GOOGLE_API_KEY)
    prompt = f"""You are an expert screenplay analyst with years of experience in the film industry. Your task is to provide a comprehensive, insightful, and actionable analysis of the given screenplay to help the writer elevate their work to a professional level. 

Screenplay: ```{screenplay_text}```

Please conduct a thorough analysis covering the following aspects:

1. Story Structure and Plot (20% of analysis):
   - Evaluate the three-act structure or alternative story structure used.
   - Identify the inciting incident, plot points, midpoint, and climax.
   - Analyze the effectiveness of the story arc and character journeys.
   - Highlight any plot holes or inconsistencies, providing specific examples and page numbers.
   - Suggest improvements to strengthen the overall narrative structure.
   - Compare the plot structure to successful films in the same genre.

2. Character Development (20% of analysis):
   - Assess the depth and arc of the protagonist, antagonist, and supporting characters.
   - Evaluate character motivations, conflicts, and relationships.
   - Analyze how character relationships evolve throughout the story.
   - Identify any stereotypes or underdeveloped characters.
   - Suggest ways to make characters more three-dimensional and compelling.

3. Dialogue and Voice (15% of analysis):
   - Analyze the authenticity and distinctiveness of each character's voice.
   - Highlight examples of strong dialogue and areas that need improvement, citing specific page numbers.
   - Assess the balance between dialogue and action.
   - Offer suggestions for making the dialogue more engaging and true to each character.
   - Compare the dialogue style to successful films in the same genre.

4. Pacing and Tension (10% of analysis):
   - Evaluate the overall pacing of the screenplay.
   - Identify any scenes that drag or feel rushed, providing page numbers.
   - Assess how well tension and conflict are maintained throughout the story.
   - Provide recommendations for improving pacing and building suspense.

5. Theme and Subtext (10% of analysis):
   - Identify the main themes and how well they are explored.
   - Analyze the use of subtext and symbolism.
   - Suggest ways to deepen thematic elements and make them more impactful.
   - Consider how these themes might resonate with the target audience.

6. Visual Storytelling and Scene Description (10% of analysis):
   - Evaluate the effectiveness of scene descriptions and action lines.
   - Assess how well the writer uses visual elements to convey the story.
   - Offer suggestions for improving the visual aspect of the screenplay.
   - Provide examples of particularly strong or weak visual storytelling, citing page numbers.

7. Worldbuilding (5% of analysis):
   - Assess the uniqueness and consistency of the story's world.
   - Evaluate how well the setting is integrated into the plot and characters.
   - Suggest ways to make the world more immersive or impactful.

8. Genre Conventions and Market Potential (5% of analysis):
   - Analyze how well the screenplay fits within its intended genre.
   - Assess its potential appeal to producers and audiences.
   - Suggest ways to enhance its marketability while maintaining artistic integrity.
   - Compare it to recent successful films in the same genre.

9. Formatting and Technical Aspects (5% of analysis):
   - Check for proper screenplay formatting.
   - Identify any technical issues that need addressing.

10. Overall Impression and Next Steps:
    - Provide a summary of the screenplay's strengths and areas for improvement.
    - Offer specific, actionable steps the writer can take to elevate the screenplay.
    - Give an overall assessment of the screenplay's potential and readiness for submission.

For each section, strive to balance criticism with praise. Provide specific examples from the screenplay, including page numbers, to illustrate your points. Offer concrete, step-by-step suggestions for improvement in each area. Your analysis should be both critical and constructive, offering encouragement alongside areas for improvement.

Please format your analysis using clear headings and subheadings for each section. Use bullet points where appropriate for clarity.
"""
    model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')
    response = model.generate_content([prompt])
    
    if response.prompt_feedback.block_reason:
        return f"Analysis was blocked. Reason: {response.prompt_feedback.block_reason}"
    
    if not response.candidates:
        return "No response was generated. The model might not have produced any output."
    
    return response.text

def main():
    st.title("Screenplay Analysis Service")

    # Payment section
    st.header("Step 1: Payment")
    amount = 0.0001  # Price for the service
    st.write(f"Price for Screenplay Analysis: {amount} SOL")

    if 'payment_link_generated' not in st.session_state:
        st.session_state.payment_link_generated = False

    if 'reference' not in st.session_state:
        st.session_state.reference = None

    if 'url' not in st.session_state:
        st.session_state.url = None

    if st.button("Generate Payment Link") or st.session_state.payment_link_generated:
        if not st.session_state.payment_link_generated:
            url, reference = generate_payment_link(amount)
            st.session_state.payment_link_generated = True
            st.session_state.reference = reference
            st.session_state.url = url
        else:
            url = st.session_state.url

        st.subheader("Payment Link:")
        st.code(url)

        qr_image_stream = create_smaller_qr(url, size=(400, 400))
        st.image(qr_image_stream)

        st.info("Please scan the QR code or use the link above to make the payment. Once you've sent the SOL, click the 'Confirm Transaction' button below.")

        if st.button("Confirm Transaction"):
            with st.spinner('Confirming transaction... This may take up to a minute.'):
                payment_status = st.empty()
                for _ in range(10):  # Wait for up to 10 seconds
                    try:
                        sign: TransactionSignature = find_reference(client, st.session_state.reference)
                        payment_status.warning("Transaction found, validating...")
                        
                        if validate_transfer(client, sign.signature, {
                            "recipient": MERCHANT_WALLET,
                            "amount": amount,
                            "reference": [st.session_state.reference]
                        }):
                            payment_status.success("Payment validated! You can now proceed to upload your screenplay.")
                            st.session_state.payment_successful = True
                            st.rerun()
                            break
                    except Exception:
                        time.sleep(1)
                        continue
                else:
                    payment_status.error("Payment not found or validated within the time limit. Please try again or contact support if you believe this is an error.")

    # Screenplay analysis section (only shown after successful payment)
    if st.session_state.get('payment_successful', False):
        st.header("Step 2: Screenplay Analysis")
        st.write("Upload your screenplay in PDF format, and our advanced AI will provide a comprehensive analysis to help improve your work.")

        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_file_path = temp_file.name

            try:
                screenplay_text = extract_text_from_pdf(temp_file_path)

                if GOOGLE_API_KEY:
                    if st.button("Analyze Screenplay"):
                        with st.spinner('Analyzing your screenplay... This may take a few minutes.'):
                            try:
                                analysis_result = analyze_screenplay(screenplay_text)
                                st.success('Analysis complete!')
                                st.write("Screenplay Analysis Result:")
                                st.markdown(analysis_result)
                            except Exception as e:
                                st.error(f"An error occurred during analysis: {str(e)}")
            finally:
                os.unlink(temp_file_path)
        else:
            st.error("Google API Key not found. Please check your environment configuration.")

if __name__ == "__main__":
    main()
