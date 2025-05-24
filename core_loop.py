# core_loop.py
import asyncio
import time
import functools # For partial
from datetime import datetime

from screen_utils import capture_and_ocr
from ai_clients import AI_CLIENTS
from output_utils import print_response, log_scraped_text, log_response # Import new logging functions
from notification_utils import send_notification
from email_utils import send_email
from config import LOG_FILE

# Dictionary to store current scraped text per capture ID (needed for email body)
capture_scraped_text = {}
# Counter for unique capture IDs
capture_counter = 0

def handle_ai_response(model_name, capture_id, results_queue: asyncio.Queue, task: asyncio.Task):
    """
    Callback function executed when an AI task completes.
    Puts the result onto the results queue.
    """
    try:
        response_text = task.result() # Get the result from the completed task
        # Put the result onto the queue for the handler task to process
        results_queue.put_nowait((capture_id, model_name, response_text))
        # print(f"[{capture_id}] Received response from {model_name}, added to queue.") # Removed frequent print
    except Exception as e:
        error_msg = f"{model_name} Task Error: {e}"
        print(f"[{capture_id}] Error processing result from {model_name}: {e}") # Keep error print
        results_queue.put_nowait((capture_id, model_name, error_msg)) # Put error onto queue


async def handle_results(
    results_queue: asyncio.Queue,
    notify_enabled: bool,
    email_enabled: bool,
    email_recipient: str
):
    """
    Dedicated consumer task to process results from the queue as they arrive.
    Triggers output (print, file, notifications, email).
    """
    print("--- Result handler started ---") # Keep this start message
    while True:
        # Wait for an item to appear in the queue
        capture_id, model_name, response_text = await results_queue.get()

        # print(f"\n--- Processing result for capture {capture_id} from {model_name} ---") # Removed frequent print

        # 1. Print to terminal (Keep this as it's requested)
        print_response(model_name, response_text)

        # 2. Log to file
        log_response(capture_id, model_name, response_text)

        # 3. Send Notification (if enabled)
        if notify_enabled:
            subject = f"AI Response from {model_name} (Capture {capture_id})"
            # Limit notification message length for better display
            notification_message = response_text[:200] + "..." if len(response_text) > 200 else response_text
            send_notification(subject, notification_message) # This is sync, but usually fast enough

        # 4. Send Email (if enabled)
        if email_enabled and email_recipient:
            scraped_text_for_email = capture_scraped_text.get(capture_id, "Scraped text not available.")
            subject = f"AI Response from {model_name} (Capture {capture_id})"
            body = f"Captured Text for ID {capture_id}:\n---\n{scraped_text_for_email}\n---\nResponse from {model_name}:\n---\n{response_text}\n---"
            # Create a task for sending email to not block the result handler
            asyncio.create_task(send_email(email_recipient, subject, body))

        # Mark the queue item as done
        results_queue.task_done()


async def run_capture_loop(
    interval: int,
    notify_enabled: bool,
    email_enabled: bool,
    email_recipient: str,
    models_to_use: list,
    results_queue: asyncio.Queue, # Pass the queue
    capture_region: dict # Pass the selected region
):
    """
    Main loop that periodically captures the screen and triggers AI processing.
    """
    print(f"\nStarting capture loop every {interval} seconds on selected region...")
    # Initial log file clear/header (optional)
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"--- Exam Helper Demo Log Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")
            # Log the selected region
            f.write(f"Selected Capture Region: {capture_region}\n\n")

    except Exception as e:
        print(f"Error writing initial log file header {LOG_FILE}: {e}")


    while True:
        start_time = time.time()

        # Process one capture cycle
        await process_capture(
            interval, notify_enabled, email_enabled, email_recipient, models_to_use, results_queue, capture_region # Pass the region
        )

        elapsed_time = time.time() - start_time
        sleep_duration = max(0, interval - elapsed_time) # Ensure non-negative sleep

        if sleep_duration > 0:
            # Removed frequent print here
            # print(f"\nSleeping for {sleep_duration:.2f} seconds until next capture.")
            pass
        else:
            print(f"\nWarning: Processing took longer than {interval} seconds. Capturing immediately.") # Keep this warning

        await asyncio.sleep(sleep_duration)


async def process_capture(
    interval: int,
    notify_enabled: bool,
    email_enabled: bool,
    email_recipient: str,
    models_to_use: list,
    results_queue: asyncio.Queue,
    capture_region: dict # Accept the selected region
):
    """
    Performs one capture-process cycle.
    """
    global capture_counter
    capture_id = datetime.now().strftime("%Y%m%d%H%M%S") + f"_{capture_counter:03d}" # Add padding for counter
    capture_counter += 1

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Capture {capture_id}: Capturing...") # Print capture start timestamp

    # 1. Capture and OCR - Pass the selected region
    scraped_text = await capture_and_ocr(capture_region)

    if not scraped_text or "OCR Error" in scraped_text: # Basic error check, check for the specific error string
        print(f"[{capture_id}] Skipping AI processing due to OCR error or empty text.") # Keep this print
        scraped_text = scraped_text if scraped_text else "Empty Capture" # Ensure scraped_text is not None
        capture_scraped_text[capture_id] = scraped_text # Still store for potential logging context

        # Log the capture even if empty or error
        log_scraped_text(capture_id, scraped_text)
        return # Skip AI steps for this cycle

    # Store scraped text for later logging/email
    capture_scraped_text[capture_id] = scraped_text

    # Log the capture (now happens here for non-empty/error)
    log_scraped_text(capture_id, scraped_text)
    # print(f"[{capture_id}] Scraped text (first 200 chars): {scraped_text[:200]}...") # Print snippet if needed for debugging

    # 2. Send to AI Clients (Asynchronously)
    tasks = []
    for model_name in models_to_use:
        if model_name in AI_CLIENTS:
            # print(f"[{capture_id}] Sending text to {model_name}...") # Removed frequent print
            # Create a task for each AI call and pass capture_id to correlate responses
            task = asyncio.create_task(
                AI_CLIENTS[model_name](scraped_text)
            )
            # Add a callback that will put the result onto the queue
            task.add_done_callback(
                functools.partial(handle_ai_response, model_name, capture_id, results_queue)
            )
            tasks.append(task)
        else:
            print(f"[{capture_id}] Warning: Unknown AI model '{model_name}' requested.") # Keep warning

    # No need to await 'tasks' here as responses are handled by the queue/callback