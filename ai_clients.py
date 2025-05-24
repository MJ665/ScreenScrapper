# ai_clients.py
import google.generativeai as genai
import os
import asyncio # Needed for async functions
import httpx # Needed for other potential API calls
import json # Potentially needed for other APIs
from config import GOOGLE_API_KEY # Import keys from config
# Make sure GEMINI_MODEL_NAME is defined in your config.py
from config import GEMINI_MODEL_NAME

# Configure Gemini API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("Warning: GOOGLE_API_KEY not found. Gemini client will not work.")


# --- Gemini Client ---

# Define the detailed system prompt for the AI Exam Companion
# This prompt guides Gemini to analyze text from screen captures for various question types
# and provide concise, direct answers suitable for an exam setting.
GEMINI_EXAM_PROMPT = """
**SYSTEM PROMPT: AI Exam Companion**

**ROLE:** You are a highly capable and efficient AI assistant designed to quickly identify and answer questions presented in text format, extracted from screen captures during academic or technical assessments. You are an expert in:
- **Data Structures and Algorithms (DSA)** problems and concepts.
- **Aptitude** questions (Quantitative Reasoning, Logical Reasoning, Data Interpretation).
- **Computer Science Fundamentals** (e.g., Operating Systems, Databases, Networking, OOP, Theory of Computation).
- **General Knowledge** or subject-specific questions that can be answered concisely.
- **Multiple Choice Questions (MCQs)**, where you should identify the correct option.
- **Coding Problems** (similar to LeetCode, HackerRank, etc.), where you should provide a correct code solution.

**TASK:**
1.  Carefully analyze the provided text snippet, which comes from a screen capture and may contain OCR errors or imperfect formatting.
2.  Identify any explicit questions, problems, or prompts that clearly require a direct answer or solution from the subject areas listed above.
3.  For **each identified question/problem**:
    *   Provide the most concise, accurate, and direct answer possible.
    *   If it's an MCQ, state the correct option (e.g., "Option A", "B", "C", "D", or the text of the correct option if no letter is given).
    *   If it's a coding problem, provide a complete code solution. Assume Python is the preferred language unless the prompt explicitly requires another. Wrap code in markdown code blocks (```python\n...\n```).
    *   Avoid including unnecessary explanations or reasoning unless the question type inherently requires it (like a short definition).
4.  If, after analyzing the text, you **cannot find any clear, answerable question or problem** within the specified categories, respond *only* with the exact phrase: `NO_QUESTION_DETECTED`.

**CONSTRAINTS:**
- Respond *only* with the answer(s) or `NO_QUESTION_DETECTED`.
- DO NOT include introductory phrases like "The answer is:", "Here is the solution:", "Based on the text...".
- DO NOT include conversational filler, greetings, or sign-offs.
- DO NOT invent questions or attempt to interpret ambiguous phrases as questions if a clear question isn't present.
- If multiple distinct questions are found in the snippet, provide answers for all of them sequentially.

**FORMATTING:**
- Present answers clearly. For multiple questions, you can number them.
- Use markdown code blocks for code solutions.

--- TEXT TO ANALYZE ---
{text_to_analyze}
"""


async def get_gemini_response(text_to_analyze: str):
    """
    Sends text to Google Gemini using the defined exam prompt and returns a response.
    Returns None or an error message if API key is missing or call fails.
    """
    if not GOOGLE_API_KEY:
        return "Gemini Error: API key not configured."

    # Use the detailed exam prompt
    full_prompt = GEMINI_EXAM_PROMPT.format(text_to_analyze=text_to_analyze)

    try:
        # Use the model name from config.py
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)

        # Adding a timeout to prevent indefinite waiting
        # Adjust timeout if models or network are slow
        response = await asyncio.wait_for(
            model.generate_content_async(full_prompt),
            timeout=45.0 # Increased timeout slightly, especially for coding problems
        )

        # Extract text from the response
        if response and response.candidates:
            # Join parts in case the response is structured (unlikely with this prompt, but good practice)
            response_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            response_text = response_text.strip()

            # Check for the specific "no question" phrase
            if response_text == "NO_QUESTION_DETECTED":
                return "Gemini: No question found in this snippet."
            else:
                # For actual answers, just return the text directly as requested
                return f"Gemini Answer: {response_text}"

        else:
            # Handle cases where response is empty or structured unexpectedly
            # Log the raw response for debugging if needed
            raw_response_str = str(response) if response is not None else "None"
            print(f"Gemini API returned no text candidates. Raw response: {raw_response_str[:500]}...")
            return f"Gemini Error: No text response from API. Raw response snippet: {raw_response_str[:100]}"

    except genai.types.BlockedPromptException as e:
        print(f"Gemini API call blocked by safety filters: {e}")
        return f"Gemini Error: Prompt blocked by safety filters."
    except asyncio.TimeoutError:
        print("Gemini API call timed out.")
        return "Gemini Error: Request timed out."
    except Exception as e:
        print(f"Gemini API call failed: {e}")
        import traceback
        traceback.print_exc() # Print traceback for unexpected errors
        return f"Gemini Error: {type(e).__name__}: {e}"

# --- Placeholder Clients (Implement later if needed) ---
# Keep these as placeholders or implement them similar to the Gemini client

async def get_chatgpt_response(text_to_analyze: str):
    """Placeholder or implementation for ChatGPT API call."""
    # ... (implementation using httpx and OpenAI API key) ...
    await asyncio.sleep(1.0) # Simulate delay
    return "ChatGPT: [Not implemented/configured]" # Or actual response

async def get_perplexity_response(text_to_analyze: str):
    """Placeholder or implementation for Perplexity API call."""
     # ... (implementation using httpx and Perplexity API key) ...
    await asyncio.sleep(1.5) # Simulate delay
    return "Perplexity: [Not implemented/configured]" # Or actual response

# Map model names to their async functions
AI_CLIENTS = {
    "gemini": get_gemini_response,
    "chatgpt": get_chatgpt_response,
    "perplexity": get_perplexity_response,
}