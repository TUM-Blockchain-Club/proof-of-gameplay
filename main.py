import threading
import time
import requests
from pynput import keyboard
from model.src import main as video_processor

keyboard_keystrokes = []
keyboard_timestamps = []
video_keystrokes = []
video_timestamps = []

def monitor_keyboard():
    def on_press(key):
        keyboard_timestamps.append(time.time())
        keyboard_keystrokes.append(key)

    with keyboard.Listener(on_press=on_press) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            # Exit gracefully on Ctrl+C
            pass

def monitor_video():
    def on_press(key):
        video_timestamps.append(time.time())
        video_keystrokes.append(key)
    
    video_processor.main(on_press=on_press)

def compare_lists():
    # every 15 seconds, call Phala to compare keystrokes and timestamps and get attestation
    while True:
        time.sleep(15)

        url = 'https://wapo-testnet.phala.network/ipfs/'
        data = {
            'keyboard_timestamps': keyboard_timestamps,
            'keyboard_keystrokes': keyboard_keystrokes,
            'video_timestamps': video_timestamps,
            'video_keystrokes': video_keystrokes
        }
        requests.post(url + 'QmdjBG9vem9vjMgxKDxwMbcvZs9Asn73C2MAeWfejgMvQv/attest', json=data)

        keyboard_keystrokes.clear()
        keyboard_timestamps.clear()
        video_keystrokes.clear()
        video_timestamps.clear()

def main():
    thread_keyboard = threading.Thread(target=monitor_keyboard)
    thread_video = threading.Thread(target=monitor_video)
    thread_compare = threading.Thread(target=compare_lists)

    thread_keyboard.start()
    thread_video.start()
    thread_compare.start()

    # Ensure the main thread keeps running
    thread_keyboard.join()
    thread_video.join()
    thread_compare.join()
    

if __name__ == '__main__':
    main()
