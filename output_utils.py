# output_utils.py
from datetime import datetime
from config import LOG_FILE
import os

def print_response(source: str, response_text: str):
    """Prints the response from an AI source to the terminal."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Keep printing of final answers as requested, but perhaps make it clear
    print(f"\n[{timestamp}] AI Response ({source}):")
    print("-" * (len(source) + 20))
    print(response_text)
    print("-" * (len(source) + 20))

def log_scraped_text(capture_id: str, scraped_text: str):
    """Logs the scraped text for a specific capture ID."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"\n--- Capture ID: {capture_id} ({timestamp}) ---\n"
    log_entry += f"Scraped Text:\n{scraped_text}\n"
    log_entry += "--- Responses ---" # Header for responses that will be appended

    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        # print(f"--- Logged scraped text for capture {capture_id} to {LOG_FILE} ---") # Removed frequent print
    except Exception as e:
        print(f"Error writing scraped text to log file {LOG_FILE}: {e}")

def log_response(capture_id: str, source: str, response_text: str):
    """Logs an AI response for a specific capture ID."""
    log_entry = f"\nResponse from {source}:\n{response_text}\n---\n"

    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        # print(f"--- Logged response from {source} for capture {capture_id} to {LOG_FILE} ---") # Removed frequent print
    except Exception as e:
        print(f"Error writing response from {source} to log file {LOG_FILE}: {e}")