# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY_ANALYZER")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
# Add placeholders for others later
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Placeholder
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY") # Placeholder

# Email Configuration
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587)) # Default to 587 if not set
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true" # Default to True

# File Output
LOG_FILE = "scraped_content.txt"

# Tesseract Path (Update if Tesseract is not in your PATH)
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")