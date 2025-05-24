# main.py
import asyncio
import sys
import threading # For pynput listener
import time
from datetime import datetime
from pynput import mouse # Import mouse listener
import re # For basic email validation
import platform # To check OS for specific notes

# Import core functions and configurations
from core_loop import run_capture_loop, handle_results
from config import LOG_FILE, GOOGLE_API_KEY, OPENAI_API_KEY, PERPLEXITY_API_KEY
from ai_clients import AI_CLIENTS # To check which clients are potentially available

# Global variables for mouse listener
click_coords = []
listener = None

def on_click(x, y, button, pressed):
    """Mouse listener callback to capture click coordinates."""
    if pressed:
        # Cast coordinates to integers immediately
        int_x, int_y = int(x), int(y)
        print(f"Click detected at ({int_x}, {int_y})")
        click_coords.append((int_x, int_y))
        if len(click_coords) == 2:
            # Stop the listener after the second click
            print("Second click captured. Stopping listener.")
            global listener
            if listener:
                # Use call_soon_threadsafe to stop the listener from another thread
                asyncio.get_event_loop().call_soon_threadsafe(listener.stop)
            return False # Signal listener thread to stop


def get_screen_region():
    """Guides user to select a screen region with mouse clicks."""
    global click_coords, listener
    click_coords = [] # Reset clicks

    print("\n--- Screen Region Selection ---")
    print("Instructions: Use your mouse to define the area you want to capture.")
    print("1. Click the top-left corner of the desired area.")
    print("2. Click the bottom-right corner of the desired area.")
    print("Click anywhere else to restart selection if needed.")

    # Start listening in a separate thread
    # Use daemon=True so the thread doesn't prevent the main script from exiting
    listener = mouse.Listener(on_click=on_click)
    listener.daemon = True
    listener.start()

    print("Waiting for clicks...")
    # We need a way to wait for the clicks without blocking the main async loop start immediately.
    # A simple time.sleep is problematic in async. A better way is to check the condition periodically.
    # Or, since this happens *before* the main asyncio loop starts, listener.join() is okay here.
    # However, the listener thread needs the main loop context to stop gracefully via call_soon_threadsafe.
    # Let's just block briefly in a loop checking the condition.

    # Use an event or a simple loop check to wait for clicks outside the async loop
    # Since this happens before asyncio.run(main()), we can block here.
    # But the listener needs the loop reference to call call_soon_threadsafe.
    # Let's restructure get_screen_region to be called *inside* the async main or handle the loop reference.
    # Alternative: Use a Future/Event or a simple loop with small sleep.

    # Simpler approach for pre-loop setup: Just check len(click_coords) in a loop.
    # The call_soon_threadsafe ensures the listener stops correctly.
    while len(click_coords) < 2:
        time.sleep(0.1) # Wait briefly to avoid busy-looping too hard

    # The listener is stopped by the callback via call_soon_threadsafe
    # We don't necessarily need listener.join() here if we are confident the callback stops it.
    # Let's add a small sleep to allow the stop call to potentially process.
    time.sleep(0.5)


    if len(click_coords) == 2:
        (x1, y1) = click_coords[0]
        (x2, y2) = click_coords[1]

        # Calculate the region dictionary using integer coordinates
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        # Ensure width and height are at least 1 pixel
        width = max(1, width)
        height = max(1, height)

        region = {'top': top, 'left': left, 'width': width, 'height': height}
        print(f"Selected region: {region}")
        return region
    else:
        print("Region selection failed. Please try again.")
        # This recursive call might stack up if failures persist.
        # For a demo, maybe just exit or return None/default region on repeated failure?
        # Let's add a simple retry counter.
        return get_screen_region_with_retry() # Call a new function with retry


def get_screen_region_with_retry(retries=3):
     for i in range(retries):
         region = get_screen_region() # Call the actual selection logic
         if region and region['width'] > 0 and region['height'] > 0:
              return region
         print(f"Attempt {i+1}/{retries} failed. Trying again...")
     print("Failed to select region after multiple attempts. Exiting.")
     sys.exit(1) # Exit if selection fails after retries


def get_user_input():
    """Prompts user for configuration settings."""
    print("--- Exam Helper Demo Configuration ---")

    # --- Admin/Background Concept Note ---
    print("\nNOTE for Educational Demo:")
    print("This script simulates a 'background admin' cheat tool for educational purposes ONLY.")
    print("To truly operate undetected with elevated privileges in the background, it would involve")
    print("complex OS-specific techniques (like compiled executables, registering as a service,")
    print("handling user sessions, bypassing security prompts). This Python script demonstrates")
    print("the core capture, analysis, and output logic, but runs visibly in the terminal and")
    print("process list. Running it 'as administrator' on Windows would grant privileges,")
    print("but doesn't make it invisible.")
    # Add macOS specific permission note for the click method
    if platform.system() == "Darwin": # Check if on macOS
         print("\n--- macOS Permissions Required for Click Selection ---")
         print("On macOS, you must grant 'Accessibility' permissions to the terminal (or Python executable)")
         print("running this script for mouse click detection to work.")
         print("Go to: System Settings > Privacy & Security > Accessibility")
         print("Drag your Terminal app (or VS Code) into the list and enable it.")
         print("You may also need to enable notifications under 'Notifications' settings.")
         print("You might also need to install pyobjc: pip install pyobjc")
         print("-" * 40) # Separator for macOS note
    else:
         print("-" * 40) # Separator for general note


    while True:
        try:
            interval = int(input("Enter screen capture interval in seconds (e.g., 20): "))
            if interval <= 0:
                print("Interval must be a positive number.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

    while True:
        notify_input = input("Enable desktop notifications? (yes/no): ").lower()
        if notify_input in ['yes', 'y']:
            notify_enabled = True
            # Note about potential notification issues on some systems
            print("Note: Desktop notifications might require OS permissions or dependencies.")
            break
        elif notify_input in ['no', 'n']:
            notify_enabled = False
            break
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

    while True:
        email_input = input("Enable email notifications? (yes/no): ").lower()
        if email_input in ['yes', 'y']:
            email_enabled = True
            while True:
                email_recipient = input("Enter recipient email address: ")
                # More robust email format check
                if re.match(r"[^@]+@[^@]+\.[^@]+", email_recipient):
                    break
                else:
                    print("Invalid email format. Please try again.")
            break
        elif email_input in ['no', 'n']:
            email_enabled = False
            email_recipient = None
            break
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

    models_to_use = []
    print("\nChoose which AI models to use (enter 'yes' or 'no' for each):")

    # Check availability and ask for each model
    if GOOGLE_API_KEY:
         while True:
            use_gemini = input("Use Google Gemini? (yes/no): ").lower()
            if use_gemini in ['yes', 'y']:
                models_to_use.append("gemini")
                break
            elif use_gemini in ['no', 'n']:
                 break
            else:
                 print("Invalid input. Please enter 'yes' or 'no'.")
    else:
         print("Google Gemini API key not configured in .env. Skipping Gemini.")

    # Add checks for other keys and prompt if available (placeholders)
    if OPENAI_API_KEY:
         while True:
            use_chatgpt = input("Use OpenAI ChatGPT? (yes/no): ").lower()
            if use_chatgpt in ['yes', 'y']:
                models_to_use.append("chatgpt")
                break
            elif use_chatgpt in ['no', 'n']:
                 break
            else:
                 print("Invalid input. Please enter 'yes' or 'no'.")
    else:
         print("OpenAI API key not configured in .env. Skipping ChatGPT.")

    if PERPLEXITY_API_KEY:
         while True:
            use_perplexity = input("Use Perplexity? (yes/no): ").lower()
            if use_perplexity in ['yes', 'y']:
                models_to_use.append("perplexity")
                break
            elif use_perplexity in ['no', 'n']:
                 break
            else:
                 print("Invalid input. Please enter 'yes' or 'no'.")
    else:
         print("Perplexity API key not configured in .env. Skipping Perplexity.")


    if not models_to_use:
        print("\nError: No AI models selected or configured. Cannot run the demo.")
        sys.exit(1) # Exit if no models are available/selected

    # Get the screen region using the click method
    capture_region = get_screen_region_with_retry() # Use the retry function


    print("\n--- Configuration Summary ---")
    print(f"Capture Interval: {interval} seconds")
    print(f"Capture Region: {capture_region}")
    print(f"Desktop Notifications: {'Enabled' if notify_enabled else 'Disabled'}")
    if notify_enabled and platform.system() == "Darwin":
        print("Note: Notifications still require macOS permissions (see above) and 'pyobjc'.")
    elif notify_enabled:
        print("Note: Desktop notifications may not work depending on OS permissions/setup.")

    print(f"Email Notifications: {'Enabled' if email_enabled else 'Disabled'}")
    if email_enabled:
        print(f"Email Recipient: {email_recipient}")
    print(f"AI Models Enabled: {', '.join(models_to_use)}")
    print(f"Output Log File: {LOG_FILE}")
    print("-" * 30)
    print("Starting the demo. Press Ctrl+C to stop.")
    print("Remember this is for educational demonstration only.")


    return interval, notify_enabled, email_enabled, email_recipient, models_to_use, capture_region


# Rest of main.py (main async function and __main__ block) remains the same
async def main():
    """Main asynchronous function to get input, select region, and start the loops."""
    interval, notify_enabled, email_enabled, email_recipient, models_to_use, capture_region = get_user_input()

    # Create an asyncio Queue to pass results from AI tasks to the handler
    results_queue = asyncio.Queue()

    # Start the result handler task
    result_handler_task = asyncio.create_task(
        handle_results(results_queue, notify_enabled, email_enabled, email_recipient)
    )

    # Start the main capture and processing loop task - Pass the capture_region
    capture_loop_task = asyncio.create_task(
        run_capture_loop(interval, notify_enabled, email_enabled, email_recipient, models_to_use, results_queue, capture_region)
    )

    # Keep the main loop running indefinitely until interrupted
    try:
        # This will run until one of the tasks finishes (which they won't, unless error)
        # or until cancelled (e.g., by Ctrl+C)
        await asyncio.gather(capture_loop_task, result_handler_task)
    except asyncio.CancelledError:
        print("\nShutting down Exam Helper Demo...")
    finally:
        # Clean up tasks on shutdown
        capture_loop_task.cancel()
        result_handler_task.cancel()
        # Give tasks a moment to clean up if needed
        await asyncio.sleep(1.0)
        print("Background tasks likely stopped.")
        # try:
        #     # Gathering again with return_exceptions=True can help if cancel didn't fully stop them
        #     await asyncio.gather(capture_loop_task, result_handler_task, return_exceptions=True)
        # except:
        #      pass # Ignore exceptions during final cleanup

if __name__ == "__main__":
    # Need to handle KeyboardInterrupt (Ctrl+C) gracefully
    try:
        # Run the main async function
        # We need the event loop to be created before the mouse listener callback tries to use it
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main()) # Use run_until_complete instead of asyncio.run for loop access
    except KeyboardInterrupt:
        print("\nDemo stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        
        
        