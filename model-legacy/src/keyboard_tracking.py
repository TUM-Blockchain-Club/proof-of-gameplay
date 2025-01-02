import cv2
import numpy as np

# Global variables to store mouse clicks
ref_points = []
calibration_complete = False

def click_event(event, x, y, flags, params):
    global ref_points, calibration_complete
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(ref_points) < 4:
            ref_points.append((x, y))
            print(f"Point selected: ({x}, {y})")
        if len(ref_points) == 4:
            calibration_complete = True

def calibrate_keyboard(cap):
    global ref_points, calibration_complete
    # cap = cv2.VideoCapture(0)  # Use the default webcam

    # if not cap.isOpened():
    #     print("Failed to open camera.")
    #     return None

    cv2.namedWindow("Calibrate Keyboard")
    cv2.setMouseCallback("Calibrate Keyboard", click_event)

    print("Please click on the four corners of the keyboard in the following order:")
    print("Top-Left, Top-Right, Bottom-Right, Bottom-Left")
    print("Press 'r' to reset the points if needed.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame from camera.")
            break

        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()

        # Draw the selected points
        for idx, point in enumerate(ref_points):
            cv2.circle(display_frame, point, 5, (0, 255, 0), -1)
            cv2.putText(display_frame, f"{idx+1}", (point[0]+10, point[1]+10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Draw lines between points if at least 2 points are selected
        if len(ref_points) >= 2:
            cv2.polylines(display_frame, [np.array(ref_points)], isClosed=False, color=(255, 0, 0), thickness=2)

        # If all four points are selected, draw the quadrilateral
        if len(ref_points) == 4:
            cv2.polylines(display_frame, [np.array(ref_points)], isClosed=True, color=(0, 0, 255), thickness=2)

        cv2.imshow("Calibrate Keyboard", display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("Calibration aborted by user.")
            ref_points = []
            calibration_complete = False
            break
        elif key == ord('r'):
            print("Resetting calibration points.")
            ref_points = []
            calibration_complete = False
        elif calibration_complete:
            print("Calibration complete.")
            break

    cv2.destroyAllWindows()

    if len(ref_points) != 4:
        print("Calibration failed. Please select exactly 4 points.")
        return None

    # Order the points correctly (if necessary)
    pts_src = np.array(ref_points, dtype='float32')

    return pts_src

def get_homography_matrix(pts_src):
    # Define the destination points for a standard keyboard size
    # For example, we can assume a keyboard size of 800x300 pixels
    width, height = 725, 300
    pts_dst = np.array([
        [0, 0],           # Top-Left
        [width, 0],       # Top-Right
        [width, height],  # Bottom-Right
        [0, height]       # Bottom-Left
    ], dtype='float32')

    # Compute the homography matrix
    h_matrix, status = cv2.findHomography(pts_src, pts_dst)
    return h_matrix, (width, height)

def warp_frame(frame, h_matrix, size):
    # Warp the input frame to the top-down view
    warped_frame = cv2.warpPerspective(frame, h_matrix, size)
    return warped_frame
