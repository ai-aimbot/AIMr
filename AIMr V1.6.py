import os
import cv2
import sys
import json
import time
import math
import pyfiglet
import requests
import keyboard
import pyautogui
import threading
import numpy as np
import win32api, win32con, win32gui, win32ui


# Check if AIMr is up to date
newest_version = "https://raw.githubusercontent.com/kbdevs/ai-aimbot/main/current_version.txt"
local_version = "V1.6"

# Launch counter
url = "https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Flocalhost%2FAIMr&count_bg=%23FF0000&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=Launches&edge_flat=false"
response = requests.get(url)


def clearfig():
        os.system('cls' if os.name == 'nt' else 'clear')
        result = pyfiglet.figlet_format("A I M r", font="3-d")
        print("\u001b[35m" + result + "\u001b[0m")
        response = requests.get(newest_version, headers={"Cache-Control": 'no-cache', "Pragma": "no-cache"})
        remote_version = response.text.strip()
        if remote_version != local_version:
            print("\033[91mYour version of AIMr is out of date!!\033[0m" + "\n")
        else:
            print(local_version + "\n")

def typewriter(text,option):
        for character in text:
            sys.stdout.write(character)
            sys.stdout.flush()
            if option == "logo":
                time.sleep(0.01)
            else:
                time.sleep(0.02)
        if option == "input":
            value = input()
            return value


def clearfig():
        os.system('cls' if os.name == 'nt' else 'clear')
        result = pyfiglet.figlet_format("A I M r", font="3-d")
        print("\u001b[35m" + result + "\u001b[0m")
        response = requests.get(newest_version, headers={"Cache-Control": 'no-cache', "Pragma": "no-cache"})
        remote_version = response.text.strip()
        if remote_version != local_version:
            print("\033[91mYour version of AIMr is out of date!!\033[0m" + "\n")
        else:
            print(local_version + "\n")

try:

    os.system('cls' if os.name == 'nt' else 'clear')

    typewriter("Loading... \n", "print")

    result = pyfiglet.figlet_format("A I M r", font="3-d")
    typewriter("\u001b[35m" + result + "\u001b[0m", "logo")
    typewriter("\nLoaded.", "print")

    time.sleep(1)

    CONFIG_FILE = './yolov4-tiny.cfg'
    WEIGHT_FILE = './yolov4-tiny.weights'

    clearfig()

    config = False

    option = True if typewriter("Do you want aimbot or a triggerbot? (1/2): ", "input").lower() == "1" else False

    if option:

        clearfig()
        show_frame = True if typewriter("Do you want to use a GUI? (y/n): ", "input").lower() == "y" else False

        clearfig()

        config_file_path = "./config.json"

        if os.path.exists(config_file_path):
            config = True if typewriter("Do you want to use a config? (y/n): ", "input").lower() == "y" else False
        else:
            exit

        clearfig()

        net = cv2.dnn.readNetFromDarknet(CONFIG_FILE, WEIGHT_FILE)
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

        ln = net.getLayerNames()
        ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

        screen_size = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

        region = 0, 0, screen_size[0], screen_size[1]

        # square_size = 540
        square_size = min(region[2], region[3]) // 2
        square_x = region[0] + (region[2] - square_size) // 2
        square_y = region[1] + (region[3] - square_size) // 2
        square_region = square_x, square_y, square_size, square_size

        locked_box = None
        frames_without_detection = 0
        max_frames_without_detection = 10



        if config:
            # Load config from config.json file
            with open('config.json') as f:
                config = json.load(f)
            floating = config.get("floating", "0")
            shoot = config.get("enable_shooting", "0")
            key = config.get("aim_key", "").lower()
            placement_side = config.get("placement_side", "").lower()
            smoothness = config.get("smoothness", 1)

            # Convert smoothness to integer
            smoothness = int(smoothness)
        else:
            if show_frame:
                floating = True if typewriter("Do you want the detection window be pinned on top? (y/n): ", "input").lower() == "y" else False
            clearfig()
            shoot = True if typewriter("Do you want it to shoot? (y/n): ", "input").lower() == "y" else False
            clearfig()
            key = typewriter("Press the key you want to use to aim: ", "input").lower()
            clearfig()
            placement_side = typewriter("Enter 'left' or 'right' or 'no' to place the detection block rectangle: ", "input").lower()
            clearfig()
            smoothness = typewriter("Smoothness? (1-10): ", "input")
            clearfig()
            smoothness = int(smoothness)
            save_config = True if typewriter("Do you want to save this config? (y/n): ", "input").lower() == "y" else False
            clearfig()
            if save_config:
                config_data = {
                    "floating": floating,
                    "enable_shooting": shoot,
                    "aim_key": key,
                    "placement_side": placement_side,
                    "smoothness": smoothness
                }
                with open('config.json', 'w') as f:
                    json.dump(config_data, f)
                    typewriter("Config file saved.", "print")
            else:
                typewriter("Config file not saved.", "print")

        clearfig()

        def movement_thread_func(x, y):
            # Move mouse towards the closest enemy
            x_smooth = x
            y_smooth = y

            current_x, current_y = win32api.GetCursorPos()
            target_x = current_x + x_smooth + 2
            target_y = current_y + y_smooth + 30

            steps = smoothness  # Number of steps for smooth movement
            delta_x = ((target_x - current_x) / steps) / 1.2
            delta_y = ((target_y - current_y) / steps) / 1.2

            if abs(current_x - target_x) + abs(current_y - target_y) < 1200:
                for step in range(steps):
                    current_x += delta_x
                    current_y += delta_y
                    # Add randomization to mouse movement
                    rand_x = np.random.randint(-2, 2)
                    rand_y = np.random.randint(-2, 2)
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(delta_x) + rand_x, int(delta_y) + rand_y, 0, 0)
                    time.sleep(0.005)
                if shoot:
                    shooting_thread = threading.Thread(target=shooting_thread_func)
                    shooting_thread.start()

        def movement(x, y):
            movement_thread = threading.Thread(target=movement_thread_func, args=(x, y))
            movement_thread.start()

        def shooting_thread_func():
            # Shoot
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.07)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.2)  # Delay for 0.2 seconds

        typewriter(f"Hold {key} for it to aim. \n", "print")
        typewriter("\u001b[32mRunning...\u001b[0m", "print")
        
        while True:
            start_time = time.perf_counter()
            # Get image of screen
            hwnd = win32gui.GetDesktopWindow()

            wDC = win32gui.GetWindowDC(hwnd)
            dcObj = win32ui.CreateDCFromHandle(wDC)
            cDC = dcObj.CreateCompatibleDC()

            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(dcObj, square_size, square_size)
            cDC.SelectObject(bmp)
            cDC.BitBlt((0, 0), (square_size, square_size), dcObj, (square_x, square_y), win32con.SRCCOPY)

            signed_ints_array = bmp.GetBitmapBits(True)
            frame = np.frombuffer(signed_ints_array, dtype='uint8')
            frame.shape = (square_size, square_size, 4)

            dcObj.DeleteDC()
            cDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, wDC)
            win32gui.DeleteObject(bmp.GetHandle())

            frame = frame[..., 2::-1]  # Remove the alpha channel
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

            frame_height, frame_width = frame.shape[:2]

            if placement_side == 'left':
                # Rectangle on the left side
                rect_size_y = int(round(square_size * 3/5.4))
                rect_size_x = int(round(square_size * 2/5.4))
                rect_color = (0, 0, 0)
                rect_x = 0  # Left side
                rect_y = square_size - rect_size_y
            elif placement_side == 'right':
                # Rectangle on the right side
                rect_size_y = int(round(square_size * 2.5/5.4))
                rect_size_x = int(round(square_size * 1.5/5.4))
                rect_color = (0, 0, 0)
                rect_x = square_size - rect_size_x  # Right side
                rect_y = square_size - rect_size_y
            elif placement_side == 'no':
                # Rectangle on the right side
                rect_size_y = 0
                rect_size_x = 0
                rect_color = (0, 0, 0)
                rect_x = square_size - rect_size_x  # Right side
                rect_y = square_size - rect_size_y
            else:
                typewriter("Invalid input. Please enter 'left' or 'no'.", "print")
                exit(1)

            # Add a block rectangle to the square frame
            cv2.rectangle(frame, (rect_x, rect_y), (rect_x + rect_size_x, rect_y + rect_size_y), rect_color, -1)

            # Detection loop
            blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (320, 320), crop=True)
            net.setInput(blob)
            layerOutputs = net.forward(ln)

            boxes = []
            confidences = []

            for output in layerOutputs:
                for detection in output:
                    scores = detection[5:]
                    classID = np.argmax(scores)
                    confidence = scores[classID]
                    if confidence > 0.4 and classID == 0:
                        box = detection[:4] * np.array([square_size, square_size, square_size, square_size])
                        (centerX, centerY, width, height) = box.astype("int")
                        x = int(centerX - (width / 2))
                        y = int(centerY - (height / 2))
                        box = [x, y, int(width), int(height)]
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
                    # print(f"Detected: {len(indices)}")
                    center_x = square_size // 2
                    center_y = square_size // 2

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

            if locked_box is not None and keyboard.is_pressed(key):
                movement(x, y)

            for i, box in enumerate(boxes):
                (x, y, w, h) = box
                if locked_box is not None and box == locked_box:
                    color = (0, 255, 0)  # Green color for locked box
                else:
                    color = (255, 255, 255)  # White color for other boxes

                if show_frame:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                    # Draw line from box to center of the frame
                    cv2.line(frame, (x + w // 2, y + h // 2), (square_size // 2, square_size // 2), (0, 0, 255), 2)

                    # Display confidence percentage above the box
                    confidence_text = f'{confidences[i] * 100:.2f}%'
                    text_width, text_height = cv2.getTextSize(confidence_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                    cv2.putText(frame, confidence_text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

            if show_frame:
                if floating:
                    cv2.namedWindow("Detections", cv2.WINDOW_NORMAL)
                    cv2.setWindowProperty("Detections", cv2.WND_PROP_TOPMOST, 1)
                cv2.putText(frame, f"FPS: {int(1/(time.perf_counter() - start_time))}", (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (113, 116, 244), 2)
                cv2.imshow("Detections", frame)
                cv2.waitKey(1)

    else:
        clearfig()
        key = typewriter("Enter the key you want to use to activate the triggerbot: ", "input")
        clearfig()
        delay = int(typewriter("Enter the delay (ms) you want to use for the triggerbot: ", "input"))

        clearfig()
        typewriter(f"Hold {key} for it to shoot when it notices changes. \n", "print")
        typewriter("\u001b[32mRunning...\u001b[0m", "print")

        while True:
            time.sleep(0.010)
            if keyboard.is_pressed(key):
                og_pixel_color = pyautogui.pixel(965, 538)
                pixel_color = pyautogui.pixel(965, 538)
                if abs(sum(pixel_color) - sum(og_pixel_color)) > 0.05 * sum(og_pixel_color):  # Change the condition based on the desired color
                    time.sleep((delay-10)/1000)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

except KeyboardInterrupt:
    clearfig()
    typewriter("\u001b[0m\033[91mExiting...\n\u001b[0m", "print")
    time.sleep(0.2)
