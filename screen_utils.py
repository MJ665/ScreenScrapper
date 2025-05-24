# screen_utils.py
import mss
import mss.tools
import pytesseract
from PIL import Image
import numpy as np
import io
import os
from config import TESSERACT_CMD

# Point pytesseract to your tesseract installation if it's not in your PATH
# Example for Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Example for macOS (Homebrew):
# pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract' # Adjust path based on your Homebrew prefix
# Check your installation path and uncomment/modify the line below if needed:
# pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD # Using from config

async def capture_and_ocr(region=None):
    """
    Captures the screen (full primary or specified region) and extracts text using OCR.
    Returns the extracted text.
    `region` should be a dictionary like {'top': y, 'left': x, 'width': w, 'height': h}
    """
    # Removed the frequent print statements here for 'background' feel
    # print("\n--- Capturing screen ---")
    try:
        with mss.mss() as sct:
            if region:
                # Capture the specified region
                sct_img = sct.grab(region)
                # print(f"Captured region: {region}")
            else:
                # Get a screenshot of the primary monitor if no region is specified
                monitor = sct.monitors[1] # Index 1 is usually the primary monitor
                sct_img = sct.grab(monitor)
                # print("Captured full primary screen")


            # Convert to PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

            # Perform OCR
            # Removed frequent print here too
            # print("--- Performing OCR ---")
            # Optional: Add configuration for OCR, e.g., lang='eng'
            text = pytesseract.image_to_string(img)

            # print("--- OCR Complete ---")
            # Clean up common OCR artifacts (simple example)
            text = text.strip()
            # Keep original line breaks for potential questions, but remove empty lines at start/end
            lines = text.splitlines()
            cleaned_lines = [s for s in lines if s.strip()] # Remove lines that are only whitespace
            text = "\n".join(cleaned_lines).strip() # Join back, remove overall start/end whitespace


            # print(f"Extracted text (first 200 chars): {text[:200]}...")

            return text

    except FileNotFoundError:
        error_msg = f"Error: Tesseract executable not found. Please install Tesseract OCR or set the correct path in config.py (currently '{TESSERACT_CMD}')."
        print(error_msg) # Keep essential errors printed
        return f"OCR Error: {error_msg}"
    except Exception as e:
        error_msg = f"Error during screen capture or OCR: {e}"
        print(error_msg) # Keep essential errors printed
        return f"OCR Error: {e}"