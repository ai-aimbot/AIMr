import numpy as np
import win32api, win32con, win32gui
import cv2
import math
import time
import win32ui
import keyboard
import threading
import pygetwindow as gw
import pyfiglet
import os
import json

def clearfig():
    os.system('cls' if os.name == 'nt' else 'clear')
    result = pyfiglet.figlet_format("A I M r", font="3-d")
    print(result)


CONFIG_FILE = './yolov7-tiny.cfg'
WEIGHT_FILE = './yolov7-tiny.weights'

clearfig()

show_frame = True if input("Enter 1 for GUI, or 2 for no GUI: ") == "1" else False

clearfig()

config = True if input("Enter 1 for using a config, or 2 for no config: ") == "1" else False


net = cv2.dnn.readNetFromDarknet(CONFIG_FILE, WEIGHT_FILE)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

ln = net.getLayerNames()
ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

# Get a list of all windows (including minimized)
windows = [window for window in gw.getAllTitles() if window]

# Sort windows alphabetically by title
windows.sort()

# Print a numbered list of open windows
for i, window in enumerate(windows, start=1):
    print(f"{i}: {window}")

try:
    selection = int(input("Enter the number of the window you want to select (0 to exit): "))
    
    if 1 <= selection <= len(windows):
        selected_window = gw.getWindowsWithTitle(windows[selection - 1])[0]
        print(f"Selected window: {selected_window.title}")
    elif selection == 0:
        print("Exiting the script.")
    else:
        print("Invalid selection. Please enter a valid number.")
except ValueError:
    print("Invalid input. Please enter a number.")

wintitle = selected_window.title

screen_info = gw.getWindowsWithTitle(wintitle)[0]
screen_size = screen_info.width, screen_info.height

region = 0, 0, screen_size[0], screen_size[1]

size_scale = 2

# Define the square region in the middle
square_size = min(region[2], region[3]) // 2
square_x = region[0] + (region[2] - square_size) // 2
square_y = region[1] + (region[3] - square_size) // 2
square_region = square_x, square_y, square_size, square_size

locked_box = None
frames_without_detection = 0
max_frames_without_detection = 10

if show_frame:
    cv2.namedWindow('Cropped Frame', cv2.WINDOW_NORMAL)

first_execution = True

if config:
    # Load config from config.json file
    with open('config.json') as f:
        config = json.load(f)

    shoot = config.get("enable_shooting", "0")
    key = config.get("aim_key", "").lower()
    placement_side = config.get("placement_side", "").lower()
    smoothness = config.get("smoothness", 1)

    # Convert smoothness to integer
    smoothness = int(smoothness)
else:
    shoot = input("Press 1 for to enable shooting, or anything else for just aim to be enabled: \n")
    key = input("Press the key you want to use to aim: \n").lower()
    placement_side = input("Enter 'left' or 'right' or 'no' to place the detection block rectangle: ").lower()
    smoothness = input("Smoothness? (1-10): \n")
    smoothness = int(smoothness)
    save_config = input("Do you want to save your answers to a config.json file? (y/n): ").lower()
    if save_config == "y":
        config_data = {
            "enable_shooting": shoot,
            "aim_key": key,
            "placement_side": placement_side,
            "smoothness": smoothness
        }
        with open('config.json', 'w') as f:
            json.dump(config_data, f)
            print("Config file saved.")
    else:
        print("Config file not saved.")

clearfig()

def movement_thread_func(x, y):
    # Move mouse towards the closest enemy
    scale = 1.7
    x_smooth = int(x * scale)
    y_smooth = int(y * scale)

    current_x, current_y = win32api.GetCursorPos()
    target_x = current_x + x_smooth + 2
    target_y = current_y + y_smooth + 30

    steps = smoothness  # Number of steps for smooth movement
    delta_x = ((target_x - current_x) / steps) / 1.2
    delta_y = ((target_y - current_y) / steps) / 1.2

    if keyboard.is_pressed(key):  # Check if the "1" key is held
        if abs(current_x - target_x) + abs(current_y - target_y) < 1200:
            for step in range(steps):
                current_x += delta_x
                current_y += delta_y
                # Add randomization to mouse movement
                rand_x = np.random.randint(-2, 2)
                rand_y = np.random.randint(-2, 2)
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(delta_x) + rand_x, int(delta_y) + rand_y, 0, 0)
                time.sleep(0.005)
            if shoot == "1":
                global first_execution

                if first_execution:
                    shooting_thread = threading.Thread(target=shooting_thread_func)
                    shooting_thread.start()
                    first_execution = False



def movement(x, y):
    movement_thread = threading.Thread(target=movement_thread_func, args=(x, y))
    movement_thread.start()


def shooting_thread_func():

    # Shoot
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.07)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.2)  # Delay for 0.5 seconds
    global first_execution
    first_execution = True


while True:
    # Get image of screen
    hwnd = win32gui.GetDesktopWindow()

    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()

    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(dcObj, region[2], region[3])
    cDC.SelectObject(bmp)
    cDC.BitBlt((0, 0), (region[2], region[3]), dcObj, (region[0], region[1]), win32con.SRCCOPY)

    signed_ints_array = bmp.GetBitmapBits(True)
    frame = np.frombuffer(signed_ints_array, dtype='uint8')
    frame.shape = (region[3], region[2], 4)

    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(bmp.GetHandle())

    frame = frame[..., 2::-1]  # Remove the alpha channel
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

    frame_height, frame_width = frame.shape[:2]

    # Crop frame to the square region in the middle
    square_frame = frame[square_y:square_y + square_size, square_x:square_x + square_size]
    square_frame_height, square_frame_width = square_frame.shape[:2]

  

    if placement_side == 'left':
        # Rectangle on the left side
        rect_size_y = 300
        rect_size_x = 200
        rect_color = (0, 0, 0)
        rect_x = 0  # Left side
        rect_y = square_frame_height - rect_size_y
    elif placement_side == 'right':
        # Rectangle on the right side
        rect_size_y = 250
        rect_size_x = 150
        rect_color = (0, 0, 0)
        rect_x = square_frame_width - rect_size_x  # Right side
        rect_y = square_frame_height - rect_size_y
    elif placement_side == 'no':
        # Rectangle on the right side
        rect_size_y = 0
        rect_size_x = 0
        rect_color = (0, 0, 0)
        rect_x = square_frame_width - rect_size_x  # Right side
        rect_y = square_frame_height - rect_size_y
    else:
        print("Invalid input. Please enter 'left' or 'no'.")
        exit(1)

    # Add a block rectangle to the square frame
    cv2.rectangle(square_frame, (rect_x, rect_y), (rect_x + rect_size_x, rect_y + rect_size_y), rect_color, -1)

    if show_frame:
        # Display the cropped frame in the new window
        cropped_frame = np.copy(square_frame)  # Create a copy of the cropped frame

    # Detection loop
    blob = cv2.dnn.blobFromImage(square_frame, 1 / 255.0, (320, 320), crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)

    boxes = []
    confidences = []

    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            if confidence > 0.7 and classID == 0:
                box = detection[:4] * np.array(
                    [square_frame_width, square_frame_height, square_frame_width, square_frame_height])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))
                box = [x, y, int(width), int(height)]
                # Adjust the box coordinates to the original frame
                box[0] += square_x
                box[1] += square_y
                boxes.append(box)
                confidences.append(float(confidence))

    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.4)

    if locked_box is not None:
        if locked_box not in boxes:
            frames_without_detection += 1
            if frames_without_detection >= max_frames_without_detection:
                locked_box = None
        else:
            frames_without_detection = 0

    if locked_box is None:
        if len(indices) > 0:
            clearfig()
            print(f"Detected: {len(indices)}")
            center_x = square_x + square_size // 2
            center_y = square_y + square_size // 2

            min_dist = float('inf')
            for i in indices.flatten():
                (x, y) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])

                dist = math.sqrt(math.pow(center_x - (x + w / 2), 2) + math.pow(center_y - (y + h / 2), 2))
                if dist < min_dist:
                    min_dist = dist
                    locked_box = boxes[i]

    if locked_box is not None:
        x = int(locked_box[0] + locked_box[2] / 2 - frame_width / 2)
        y = int(locked_box[1] + locked_box[3] / 2 - frame_height / 2) - locked_box[3] * 0.5  # For head shot

        movement(x, y)
        if shoot == "1":
            if keyboard.is_pressed(key):  # Check if the "1" key is held
                # Shoot

                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.07)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    # Display the cropped frame in the new window
    for i, box in enumerate(boxes):
        (x, y, w, h) = box
        if locked_box is not None and box == locked_box:
            color = (0, 255, 0)  # Green color for locked box
        else:
            color = (255, 255, 255)  # White color for other boxes

        cv2.rectangle(cropped_frame, (x - square_x, y - square_y), (x + w - square_x, y + h - square_y),
                      color, 2)

        # Draw line from box to center of the frame
        cv2.line(cropped_frame, (x - square_x + w // 2, y - square_y + h // 2), (square_size // 2, square_size // 2),
                 (0, 0, 255), 2)

        # Display confidence percentage above the box
        confidence_text = f'{confidences[i] * 100:.2f}%'
        text_width, text_height = cv2.getTextSize(confidence_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.putText(cropped_frame, confidence_text, (x - square_x, y - square_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        
    if show_frame:
        cv2.imshow("Cropped Frame", cropped_frame)
        cv2.waitKey(1)
