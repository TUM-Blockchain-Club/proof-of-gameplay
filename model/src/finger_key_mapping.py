import numpy as np
import cv2

def create_keyboard_layout(width, height):
    key_unit = 50  # Base key unit size in pixels

    horizontal_spacing = 5
    vertical_spacing = 5
    starting_x = 5
    starting_y = 5

    # Define the keyboard rows with keys and their relative widths (updated for MacBook)
    keyboard_rows = [
        # Function keys row
        [
            {'key': 'Esc', 'width': 1.5},
            {'key': 'F1', 'width': 1},
            {'key': 'F2', 'width': 1},
            {'key': 'F3', 'width': 1},
            {'key': 'F4', 'width': 1},
            {'key': 'F5', 'width': 1},
            {'key': 'F6', 'width': 1},
            {'key': 'F7', 'width': 1},
            {'key': 'F8', 'width': 1},
            {'key': 'F9', 'width': 1},
            {'key': 'F10', 'width': 1},
            {'key': 'F11', 'width': 1},
            {'key': 'F12', 'width': 1},
            {'key': 'Power', 'width': 1},
        ],
        # Number row
        [
            {'key': '^', 'width': 1},
            {'key': '1', 'width': 1},
            {'key': '2', 'width': 1},
            {'key': '3', 'width': 1},
            {'key': '4', 'width': 1},
            {'key': '5', 'width': 1},
            {'key': '6', 'width': 1},
            {'key': '7', 'width': 1},
            {'key': '8', 'width': 1},
            {'key': '9', 'width': 1},
            {'key': '0', 'width': 1},
            {'key': 'SS', 'width': 1},
            {'key': '´', 'width': 1},
            {'key': 'Delete', 'width': 1.5},
        ],
        # Top letter row
        [
            {'key': 'Tab', 'width': 1.5},
            {'key': 'Q', 'width': 1},
            {'key': 'W', 'width': 1},
            {'key': 'E', 'width': 1},
            {'key': 'R', 'width': 1},
            {'key': 'T', 'width': 1},
            {'key': 'Z', 'width': 1},
            {'key': 'U', 'width': 1},
            {'key': 'I', 'width': 1},
            {'key': 'O', 'width': 1},
            {'key': 'P', 'width': 1},
            {'key': 'UE', 'width': 1},
            {'key': '+', 'width': 1},
            {'key': 'Return', 'width': 1},
        ],
        # Middle letter row
        [
            {'key': 'CapsLock', 'width': 1.75},
            {'key': 'A', 'width': 1},
            {'key': 'S', 'width': 1},
            {'key': 'D', 'width': 1},
            {'key': 'F', 'width': 1},
            {'key': 'G', 'width': 1},
            {'key': 'H', 'width': 1},
            {'key': 'J', 'width': 1},
            {'key': 'K', 'width': 1},
            {'key': 'L', 'width': 1},
            {'key': 'OE', 'width': 1},
            {'key': 'AE', 'width': 1},
            {'key': '#', 'width': 1},
            {'key': 'Return', 'width': 0.75},
        ],
        # Bottom letter row
        [
            {'key': 'Shift', 'width': 1.25},
            {'key': '<', 'width': 1},
            {'key': 'Y', 'width': 1},
            {'key': 'X', 'width': 1},
            {'key': 'C', 'width': 1},
            {'key': 'V', 'width': 1},
            {'key': 'B', 'width': 1},
            {'key': 'N', 'width': 1},
            {'key': 'M', 'width': 1},
            {'key': ',', 'width': 1},
            {'key': '.', 'width': 1},
            {'key': '-', 'width': 1},
            {'key': 'Shift', 'width': 2.25},
        ],
        # Spacebar row
        [
            {'key': 'Fn', 'width': 1},
            {'key': 'Ctr', 'width': 1},
            {'key': 'Opt', 'width': 1},
            {'key': 'Cmd', 'width': 1.25},
            {'key': 'Space', 'width': 5},
            {'key': 'Cmd', 'width': 1.25},
            {'key': 'Opt', 'width': 1},
            {'key': 'Left', 'width': 1},
            {'key': 'Up', 'width': 1},
            {'key': 'Down', 'width': 1},
            {'key': 'Right', 'width': 1},
        ],
    ]

    # Calculate total key widths for scaling
    total_units = sum([key_info['width'] for key_info in keyboard_rows[1]])  # Using the number row as reference
    total_key_width = total_units * key_unit
    total_key_height = key_unit * len(keyboard_rows)

    # Scaling factors
    scale_x = width / total_key_width
    scale_y = height / total_key_height

    # Use the smaller scaling factor to maintain aspect ratio
    scale = min(scale_x, scale_y)

    # Adjust key sizes and positions
    keyboard_layout = []
    current_y = starting_y

    for row in keyboard_rows:
        current_x = starting_x
        for key_info in row:
            key = key_info['key']
            key_w = key_info['width'] * key_unit * scale
            key_h = key_unit * scale

            key_data = {
                'key': key,
                'x': current_x,
                'y': current_y,
                'width': key_w - horizontal_spacing * scale,
                'height': key_h - vertical_spacing * scale
            }
            keyboard_layout.append(key_data)

            current_x += key_w

        current_y += key_h

    return keyboard_layout

def map_fingertip_to_key(x, y, keyboard_layout):
    # Iterate over the keys to find which one contains the point (x, y)
    for key_info in keyboard_layout:
        x_min = key_info['x']
        x_max = key_info['x'] + key_info['width']
        y_min = key_info['y']
        y_max = key_info['y'] + key_info['height']

        if x_min <= x <= x_max and y_min <= y <= y_max:
            return key_info['key']

    return None  # No key found under the fingertip

def draw_keyboard_layout(frame, keyboard_layout):
    for key_info in keyboard_layout:
        x = int(key_info['x'])
        y = int(key_info['y'])
        w = int(key_info['width'])
        h = int(key_info['height'])
        key = key_info['key']

        # Draw the key rectangle
        cv2.rectangle(frame, (x, y), (x + w, y + h), (200, 200, 200), 1)

        # Put the key label at the center of the rectangle
        text_size = cv2.getTextSize(key, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2
        cv2.putText(frame, key, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
