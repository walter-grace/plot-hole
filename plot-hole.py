import streamlit as st
from solathon import Client, Keypair, PublicKey

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration using Streamlit secrets
try:
    MERCHANT_WALLET = PublicKey(st.secrets["solana"]["MERCHANT_WALLET"])
    CUSTOMER_WALLET_PRIVATE_KEY = st.secrets["wallet"]["CUSTOMER_WALLET_PRIVATE_KEY"]
    SOLANA_API_URL = st.secrets["solana"]["API_URL"]
    GOOGLE_API_KEY = st.secrets["api_keys"]["GOOGLE_API_KEY"]
except KeyError as e:
    st.error(f"Missing configuration: {str(e)}")
    st.error("Please check your .streamlit/secrets.toml file or Streamlit Cloud secrets configuration.")
    st.stop()

# Initialize Solana client with the API URL from secrets
client = Client(SOLANA_API_URL)

# Debug: Print the first few characters of the private key (for verification purposes only)
st.write(f"CUSTOMER_WALLET_PRIVATE_KEY (first 5 chars): {CUSTOMER_WALLET_PRIVATE_KEY[:5]}...")

try:
    CUSTOMER_WALLET = Keypair.from_private_key(bytes.fromhex(CUSTOMER_WALLET_PRIVATE_KEY))
except ValueError as e:
    st.error(f"Error creating CUSTOMER_WALLET: {str(e)}")
    st.error("Make sure CUSTOMER_WALLET_PRIVATE_KEY is a valid hexadecimal string.")
    st.stop()

# Configure Google API
import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)
