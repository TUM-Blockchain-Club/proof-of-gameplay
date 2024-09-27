import csv
import time
from pynput import keyboard

print("==========================================")
print("       Keyboard Event Logger Started       ")
print("==========================================")
print("Recording key presses and releases.")
print("Press 'Ctrl+C' to stop the logger.")
print("------------------------------------------")

# Open the CSV file for writing
with open('key_log.csv', 'w', newline='', buffering=1) as csvfile:
    fieldnames = ['timestamp', 'key-name', 'key-char', 'key-vk', 'event-type', 'duration']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    csvfile.flush()

    key_press_times = {}
    pressed_keys = set()

    # Function to handle key press events
    def on_press(key):
        timestamp = time.time()
        event_type = 'key down'

        # Identify the key
        if isinstance(key, keyboard.KeyCode):
            # For character keys
            key_id = ('char', key.char)
            key_char = key.char
            key_name = None
            key_vk = key.vk
        elif isinstance(key, keyboard.Key):
            # For special keys
            key_id = ('key', key)
            key_char = None
            key_name = key.name
            key_vk = key.value.vk
        else:
            key_id = ('unknown', key)
            key_char = None
            key_name = str(key)
            key_vk = None

        # Check if the key is already pressed
        if key_id in pressed_keys:
            # Key is already pressed, ignore this event
            return
        else:
            # Key is not pressed yet, record it
            pressed_keys.add(key_id)
            key_press_times[key_id] = timestamp

            # Record the key down event
            key_data = {
                'timestamp': timestamp,
                'key-name': key_name,
                'key-char': key_char,
                'key-vk': key_vk,
                'event-type': event_type,
                'duration': ''
            }
            writer.writerow(key_data)
            csvfile.flush()

    # Function to handle key release events
    def on_release(key):
        timestamp = time.time()
        event_type = 'key up'

        # Identify the key
        if isinstance(key, keyboard.KeyCode):
            # For character keys
            key_id = ('char', key.char)
            key_char = key.char
            key_name = None
            key_vk = key.vk
        elif isinstance(key, keyboard.Key):
            # For special keys
            key_id = ('key', key)
            key_char = None
            key_name = key.name
            key_vk = key.value.vk
        else:
            key_id = ('unknown', key)
            key_char = None
            key_name = str(key)
            key_vk = None

        # Check if the key was pressed
        if key_id in pressed_keys:
            # Calculate the duration
            press_time = key_press_times.pop(key_id, None)
            duration = timestamp - press_time if press_time else None

            # Remove the key from the set of pressed keys
            pressed_keys.remove(key_id)

            # Record the key up event
            key_data = {
                'timestamp': timestamp,
                'key-name': key_name,
                'key-char': key_char,
                'key-vk': key_vk,
                'event-type': event_type,
                'duration': duration
            }
            writer.writerow(key_data)
            csvfile.flush()
        else:
            # Key release without a corresponding key press
            pass  # Ignore or handle as needed

        # Optional: Exit on pressing ESC
        if key == keyboard.Key.esc:
            return False  # Stop listener

    # Start the keyboard listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            # Exit gracefully on Ctrl+C
            print("\nCtrl+C pressed. Exiting the key logger.")
            pass

print("------------------------------------------")
print("Key logger stopped. Log saved to 'key_log.csv'.")
