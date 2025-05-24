# ai_clients.py
import google.generativeai as genai
import os
import asyncio # Needed for async functions
import httpx # Needed for other potential API calls
import json # Potentially needed for other APIs
from config import GOOGLE_API_KEY # Import keys from config
from config import  GEMINI_MODEL_NAME
# Configure Gemini API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("Warning: GOOGLE_API_KEY not found. Gemini client will not work.")

# --- Gemini Client ---

# Define the system prompt for the educational cheat demo
# This prompt is designed to analyze text for questions and provide direct answers.
GEMINI_EXAM_PROMPT = """
You are an AI assistant designed to help users answer questions based on provided text snippets.
Analyze the following text carefully.
Identify any explicit questions, problems, or prompts that require an answer.
Provide a concise and direct answer for *each* identified question based on your general knowledge.
If you cannot find any clear question or prompt in the text, respond *only* with the phrase "NO_QUESTION_DETECTED".
Do NOT invent questions. Only answer what is explicitly asked.
Do NOT include any conversational filler, explanations, or disclaimers in your response unless no question is detected.
Just the answer(s) or "NO_QUESTION_DETECTED".

--- Text Snippet to Analyze ---
{text_to_analyze}
"""
# GEMINI_EXAM_PROMPT = """
# You are an expert interview assistant designed to help candidates prepare for hiring assessments.
# These assessments may include:

# - Aptitude questions (quantitative, logical reasoning, data interpretation, etc.)
# - Coding challenges (algorithms, data structures, code tracing, bug fixing)
# - Computer Science fundamentals (OOP, DBMS, OS, Networking, CN)
# - Behavioral and situational judgment questions

# Your task is to:

# 1. Carefully analyze the provided text.
# 2. Identify any **explicit questions or problems** (whether aptitude, coding, or theory).
# 3. For each identified question, provide:
#    - A **concise and accurate solution or answer**
#    - If applicable, also give **brief reasoning, code**, or steps used to arrive at the answer
# 4. If **no clear question is found**, respond *only* with: **"NO_QUESTION_DETECTED"**

# ⚠️ Rules:
# - DO NOT make up questions.
# - DO NOT add explanations unless they are directly supporting an answer.
# - DO NOT output conversational fluff.

# Format:
# Answer each question found in the text, numbered if multiple.

# --- Text to Analyze ---
# {text_to_analyze}
# """


async def get_gemini_response(text_to_analyze: str):
    """
    Sends text to Google Gemini and returns a response.
    Returns None or an error message if API key is missing or call fails.
    """
    if not GOOGLE_API_KEY:
        return "Gemini Error: API key not configured."

    full_prompt = GEMINI_EXAM_PROMPT.format(text_to_analyze=text_to_analyze)

    try:
        # Use a reliable model for text generation, 1.5 Flash is usually good and fast
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)

        # Adding a timeout to prevent indefinite waiting
        response = await asyncio.wait_for(
            model.generate_content_async(full_prompt),
            timeout=30.0 # Timeout after 30 seconds
        )

        # Extract text from the response
        if response and response.candidates:
            # Join parts in case the response is structured (unlikely with this prompt)
            response_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            response_text = response_text.strip()

            # Check for the specific "no question" phrase
            if response_text == "NO_QUESTION_DETECTED":
                return "Gemini: No question found in this snippet."
            else:
                return f"Gemini Answer: {response_text}"

        else:
            # Handle cases where response is empty or structured unexpectedly
            return f"Gemini Error: No text response from API. Raw response: {response}"

    except genai.types.BlockedPromptException as e:
        return f"Gemini Error: Prompt blocked by safety filters - {e}"
    except asyncio.TimeoutError:
        return "Gemini Error: Request timed out."
    except Exception as e:
        print(f"Gemini API call failed: {e}")
        return f"Gemini Error: {e}"

# --- Placeholder Clients (Implement later if needed) ---

async def get_chatgpt_response(text_to_analyze: str):
    """Placeholder for ChatGPT API call."""
    # You would add OpenAI API key check and httpx call here
    # Example using httpx (install httpx):
    # if not OPENAI_API_KEY:
    #     return "ChatGPT Error: API key not configured."
    # try:
    #     async with httpx.AsyncClient() as client:
    #         response = await client.post(
    #             "https://api.openai.com/v1/chat/completions",
    #             headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
    #             json={
    #                 "model": "gpt-3.5-turbo", # or "gpt-4"
    #                 "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": text_to_analyze}],
    #                 "max_tokens": 150
    #             },
    #             timeout=30.0
    #         )
    #         response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
    #         data = response.json()
    #         return f"ChatGPT Answer: {data['choices'][0]['message']['content'].strip()}"
    # except Exception as e:
    #     return f"ChatGPT Error: {e}"

    await asyncio.sleep(1) # Simulate network delay
    return "ChatGPT: [Not implemented yet - Placeholder]"

async def get_perplexity_response(text_to_analyze: str):
    """Placeholder for Perplexity API call."""
     # You would add Perplexity API key check and httpx call here
     # Perplexity also has an API compatible with OpenAI structure
     # Example using httpx:
     # if not PERPLEXITY_API_KEY:
     #     return "Perplexity Error: API key not configured."
     # try:
     #     async with httpx.AsyncClient() as client:
     #         response = await client.post(
     #             "https://api.perplexity.ai/chat/completions", # Check actual endpoint
     #             headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
     #             json={
     #                 "model": "llama-3-70b-instruct", # or other model
     #                 "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": text_to_analyze}],
     #                 "max_tokens": 150
     #             },
     #             timeout=30.0
     #         )
     #         response.raise_for_status()
     #         data = response.json()
     #         return f"Perplexity Answer: {data['choices'][0]['message']['content'].strip()}"
     # except Exception as e:
     #      return f"Perplexity Error: {e}"

    await asyncio.sleep(1.5) # Simulate network delay
    return "Perplexity: [Not implemented yet - Placeholder]"

# Map model names to their async functions
AI_CLIENTS = {
    "gemini": get_gemini_response,
    "chatgpt": get_chatgpt_response,
    "perplexity": get_perplexity_response,
}