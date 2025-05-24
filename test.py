import platform
import subprocess

def send_notification(title, message):
    try:
        # Try plyer first
        from plyer import notification
        notification.notify(title=title, message=message, timeout=5)
    except Exception as e:
        print(f"Plyer failed: {e}")
        os_name = platform.system()

        # macOS fallback using osascript
        if os_name == "Darwin":
            try:
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ])
            except Exception as err:
                print(f"macOS fallback failed: {err}")

        # Windows fallback using win10toast
        elif os_name == "Windows":
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5)
            except ImportError:
                print("win10toast not installed. Install with: pip install win10toast")
            except Exception as err:
                print(f"Windows fallback failed: {err}")
        else:
            print("Unsupported platform.")

# 🔔 Example Usage
send_notification("Test Notification", "This works on macOS and Windows!")
