import numpy as np
import win32api, win32con, win32gui
import cv2
import math
import time
import win32ui
import keyboard
import threading

CONFIG_FILE = './yolov7-tiny.cfg'
WEIGHT_FILE = './yolov7-tiny.weights'

net = cv2.dnn.readNetFromDarknet(CONFIG_FILE, WEIGHT_FILE)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

ln = net.getLayerNames()
ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

# Get rect of Window
hwnd = win32gui.FindWindow(None, 'Counter-Strike: Global Offensive - Direct3D 9')
rect = win32gui.GetWindowRect(hwnd)
region = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]

size_scale = 2

# Define the square region in the middle
square_size = min(region[2], region[3]) // 2
square_x = region[0] + (region[2] - square_size) // 2
square_y = region[1] + (region[3] - square_size) // 2
square_region = square_x, square_y, square_size, square_size

locked_box = None
frames_without_detection = 0
max_frames_without_detection = 10

cv2.namedWindow('Cropped Frame', cv2.WINDOW_NORMAL)

shoot = input("1 for shoot 2 for no: \n")

def movement_thread_func(x, y):
    # Move mouse towards the closest enemy
    scale = 1.7
    x_smooth = int(x * scale)
    y_smooth = int(y * scale)

    current_x, current_y = win32api.GetCursorPos()
    target_x = current_x + x_smooth + 2
    target_y = current_y + y_smooth + 35

    steps = 5  # Number of steps for smooth movement
    delta_x = ((target_x - current_x) / steps) / 1.5
    delta_y = ((target_y - current_y) / steps) / 1.5
    if keyboard.is_pressed('1'):  # Check if the "1" key is held
        if (current_x - target_x) + (current_x - target_x) < 800:
            for step in range(steps):
                current_x += delta_x
                current_y += delta_y
                # Add randomization to mouse movement
                rand_x = np.random.randint(-2, 2)
                rand_y = np.random.randint(-2, 2)
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(delta_x) + rand_x, int(delta_y) + rand_y, 0, 0)
                time.sleep(0.00000000000000000000000000000000000000001)

            
                

                

def movement(x, y):
    movement_thread = threading.Thread(target=movement_thread_func, args=(x, y))
    movement_thread.start()


while True:
    # Get image of screen
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    save_bitmap = win32ui.CreateBitmap()
    save_bitmap.CreateCompatibleBitmap(mfc_dc, region[2], region[3])

    save_dc.SelectObject(save_bitmap)
    save_dc.BitBlt((0, 0), (region[2], region[3]), mfc_dc, (region[0], region[1]), win32con.SRCCOPY)

    signed_ints_array = save_bitmap.GetBitmapBits(True)
    frame = np.frombuffer(signed_ints_array, dtype='uint8')
    frame.shape = (region[3], region[2], 4)

    mfc_dc.DeleteDC()
    save_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)
    win32gui.DeleteObject(save_bitmap.GetHandle())

    frame = frame[..., 2::-1]  # Remove the alpha channel
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

    frame_height, frame_width = frame.shape[:2]

    # Crop frame to the square region in the middle
    square_frame = frame[square_y:square_y + square_size, square_x:square_x + square_size]
    square_frame_height, square_frame_width = square_frame.shape[:2]

    # Add a block rectangle to the square frame
    rect_size_y = 250  # Size of the rectangle
    rect_size_x = 150  # Size of the rectangle
    rect_color = (0, 0, 0)  # Color of the rectangle (in BGR format)
    rect_x = square_frame_width - rect_size_x  # X-coordinate of the top-left corner of the rectangle
    rect_y = square_frame_height - rect_size_y  # Y-coordinate of the top-left corner of the rectangle
    cv2.rectangle(square_frame, (rect_x, rect_y), (rect_x + rect_size_x, rect_y + rect_size_y), rect_color, -1)

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

        movement(x,y)
        if shoot == "1":
            if keyboard.is_pressed('1'):  # Check if the "1" key is held
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
        


    cv2.imshow("Cropped Frame", cropped_frame)
    cv2.waitKey(1)