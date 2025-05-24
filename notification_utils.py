# notification_utils.py
from plyer import notification
import platform
import sys # Import sys

def send_notification(title, message):
    """
    Sends a desktop notification.
    May require specific setup and permissions on different OS.
    """
    # print(f"Attempting to send notification: {title} - {message}") # Optional debug print
    try:
        notification.notify(
            title=title,
            message=message,
            app_name='ExamHelperDemo', # App name might be shown on some systems
            # app_icon='path/to/icon.ico', # Optional: add an icon path here
            timeout=10 # Notification stays for 10 seconds
        )
    except Exception as e:
        error_msg = f"Failed to send desktop notification: {e}"
        if platform.system() == "Darwin": # Check if on macOS
             error_msg += "\nOn macOS, this often requires granting 'Accessibility' and 'Notifications' permissions to the terminal or Python app running the script, and potentially installing 'pyobjc' (`pip install pyobjc`)."
        elif platform.system() == "Linux":
             error_msg += "\nOn Linux, this might require 'dbus-python' and a notification daemon (like notify-osd or dunst)."
        print(error_msg) # Print the specific error