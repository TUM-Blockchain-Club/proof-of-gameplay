import csv
import time
from pynput import keyboard

# Function to handle key press events
def on_press(key):
    timestamp = time.time()
    try:
        # Write the character key
        writer.writerow({'timestamp': timestamp, 'key-value': key.char})
    except AttributeError:
        # Write the special key (e.g., ctrl, alt, etc.)
        writer.writerow({'timestamp': timestamp, 'key-value': str(key)})
    csvfile.flush()  # Ensure data is written to the file immediately

# Open the CSV file for writing
with open('key_log.csv', 'w', newline='', buffering=1) as csvfile:
    fieldnames = ['timestamp', 'key-value']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    csvfile.flush()

    # Start the keyboard listener
    with keyboard.Listener(on_press=on_press) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            # Exit gracefully on Ctrl+C
            pass

