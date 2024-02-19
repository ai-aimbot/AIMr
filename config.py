from customtkinter import *
from CTkColorPicker import *
import customtkinter
import json
import time
import os

# customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
# customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green
customtkinter.set_default_color_theme("theme.json")
app = customtkinter.CTk()  # create CTk window like you do with the Tk window
app.title("AIMr")
app.iconbitmap("AIMr.ico")
app.attributes("-topmost", True)
padding = 10


try:

    config_file = "config.json"

    with open("localv.json", "r") as file:
        data8 = json.load(file)
        language = data8["language"]

    # Read the lang.json file
    with open("lang.json", "r", encoding='utf-8') as file:
        data5 = json.load(file)
        # Modify the English field in the answer field
        useranswer = data5["language"].get(language, {}).get("answers", {}).get("1", "")

    def questions(list):
        with open("lang.json", "r", encoding='utf-8') as file:
            question = json.load(file)
        text = question["language"][language]["text"]
        text = text[list]
        return text

    # def toggle_window():
    #     if app.state() == "withdrawn":
    #         app.deiconify()
    #     else:
    #         app.state("withdrawn")

    # guikeyentry = customtkinter.CTkEntry(aimtab, placeholder_text=questions(0), width=240)
    # guikeyentry.pack(pady=padding, padx=padding, anchor="w")

    # def guikeyfunc():
    #     key = guikeyentry.get()
    #     data = {"gui_key": key}
    #     with open("config.json", "r+") as file:
    #         data = json.load(file)
    #         data["gui_key"] = key
    #         file.seek(0)
    #         json.dump(data, file)
    #         file.truncate()
    #     print("Set gui key")
    #     guikeyentry.delete(0, 'end')  # Clear the guikey entry

    # guikeybutton = customtkinter.CTkButton(aimtab, text=questions(1), command=guikeyfunc)
    # guikeybutton.pack(pady=padding, padx=padding, anchor="w")

    # def get_gui_key():
    #     try:
    #         with open("config.json", "r") as file:
    #             data = json.load(file)
    #             return data.get("gui_key", "")
    #         # If key is not found, do something
    #     except:
    #         with open("config.json", "w") as file:
    #             data = {"gui_key": "o"}
    #             json.dump(data, file)
    #         print("Set gui key")
    #         return "o"

    # keyboard.on_press_key(get_gui_key(), lambda _: toggle_window())

    def replace_string_in_json(string1, string2):
        file_path = "theme.json"
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Recursively replace string1 with string2 in the JSON data
        def recursive_replace(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    obj[key] = recursive_replace(value)
            elif isinstance(obj, list):
                for i in range(len(obj)):
                    obj[i] = recursive_replace(obj[i])
            elif isinstance(obj, str):
                obj = obj.replace(string1, string2)
            return obj

        # Update the data with the replaced strings
        data = recursive_replace(data)

        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)

    tabview = CTkTabview(master=app)
    tabview.pack(padx=20, pady=20)


    generaltab = tabview.add("General")
    aimtab = tabview.add("Aimbot")
    trigtab = tabview.add("Triggerbot")

    def ask_color():
        pick_color = AskColor() # open the color picker
        color = pick_color.get() # get the color string
        hex_color = color
        factor = 0.6
        # Convert hex to RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)

        # Darken the color by applying the factor to each RGB component
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

        # Ensure values are within the valid RGB range (0-255)
        r = min(max(r, 0), 255)
        g = min(max(g, 0), 255)
        b = min(max(b, 0), 255)

        # Convert back to hex
        darkened_hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
        colorbutton.configure(fg_color=color, hover_color=darkened_hex_color)
        # Read the theme.json file
        with open("theme.json", "r") as file:
            theme_data = json.load(file)

        # Get the values of fg_color and hover_color under aimrconfig
        fg_color = theme_data["AIMrconfig"]["fg_color"]
        hover_color = theme_data["AIMrconfig"]["hover_color"]
        replace_string_in_json(fg_color, hex_color)
        replace_string_in_json(hover_color, darkened_hex_color)


    def options():
        option = optionsswitch.get()
        with open("config.json", "r+") as file:
            data = json.load(file)
            data["aimbot"] = option
            file.seek(0)
            json.dump(data, file)
            file.truncate()


    # Create a switch for "Do you want aimbot or a triggerbot? (1/2):"
    optionsvar = customtkinter.StringVar(value="")
    optionsswitch = customtkinter.CTkSwitch(generaltab, text=questions(2), command=options, variable=optionsvar, onvalue=False, offvalue=True)
    optionsswitch.pack(pady=padding, padx=padding, anchor="w")


    def rpcfunc():
        option = rpcswitch.get()
        with open("config.json", "r+") as file:
            data = json.load(file)
            data["rpc"] = option
            file.seek(0)
            json.dump(data, file)
            file.truncate()

    # Create a switch for "Do you want aimbot or a triggerbot? (1/2):"
    rpcvar = customtkinter.StringVar(value="")
    rpcswitch = customtkinter.CTkSwitch(generaltab, text=questions(13), command=rpcfunc, variable=rpcvar, onvalue=True, offvalue=False)
    rpcswitch.pack(pady=padding, padx=padding, anchor="w")

    colorbutton = customtkinter.CTkButton(master=generaltab, text="Change GUI Colors (Restart to set)", command=ask_color)
    colorbutton.pack(padx=30, pady=20)

    def detection():
        option = detectionswitch.get()
        with open("config.json", "r+") as file:
            data = json.load(file)
            data["detection"] = option
            file.seek(0)
            json.dump(data, file)
            file.truncate()

    # Create a switch for "Do you want it to shoot? (y/n):"
    detectionvar = customtkinter.StringVar(value="on")
    detectionswitch = customtkinter.CTkSwitch(aimtab, text=questions(11), variable=detectionvar,command=detection, onvalue=True, offvalue=False)
    detectionswitch.pack(pady=padding, padx=padding, anchor="w")

    def pinned():
        option = pinnedswitch.get()
        with open("config.json", "r+") as file:
            data = json.load(file)
            data["pinned"] = option
            file.seek(0)
            json.dump(data, file)
            file.truncate()

    # Create a switch for "Do you want the detection window to be pinned on top? (y/n):"
    pinnedvar = customtkinter.StringVar(value="on")
    pinnedswitch = customtkinter.CTkSwitch(aimtab, text=questions(3), variable=pinnedvar, command=pinned, onvalue=True, offvalue=False)
    pinnedswitch.pack(pady=padding, padx=padding, anchor="w")


    def shoot():
        option = shootswitch.get()
        with open("config.json", "r+") as file:
            data = json.load(file)
            data["shoot"] = option
            file.seek(0)
            json.dump(data, file)
            file.truncate()

    # Create a switch for "Do you want it to shoot? (y/n):"
    shootvar = customtkinter.StringVar(value="on")
    shootswitch = customtkinter.CTkSwitch(aimtab, text=questions(4), variable=shootvar,command=shoot, onvalue=True, offvalue=False)
    shootswitch.pack(pady=padding, padx=padding, anchor="w")

    # Create a switch for "Press the key you want to use to aim:"
    aimkeyentry = customtkinter.CTkEntry(aimtab, placeholder_text=questions(5), width=190)
    aimkeyentry.pack(pady=padding, padx=padding, anchor="w")

    def aimkeyfunc():
        key2 = aimkeyentry.get()
        data2 = {"gui_key": key2}
        with open("config.json", "r+") as file:
            data2 = json.load(file)
            data2["aimkey"] = key2
            file.seek(0)
            json.dump(data2, file)
            file.truncate()
        aimkeyentry.delete(0, 'end')  # Clear the guikey entry

    aimkeybutton = customtkinter.CTkButton(aimtab, text=questions(10), command=aimkeyfunc)
    aimkeybutton.pack(pady=padding, padx=padding, anchor="w")



    # Create a switch for "Smoothness? (1-10):"
    def slider_event(value):
        key2 = value
        with open("config.json", "r+") as file:
            data2 = json.load(file)
            data2["side"] = key2
            file.seek(0)
            json.dump(data2, file)
            file.truncate()

    sidelabel = customtkinter.CTkLabel(aimtab, text=questions(6), fg_color="transparent")
    sidelabel.pack(pady=padding, padx=padding, anchor="w")
    sideslider = customtkinter.CTkSlider(aimtab, from_=1, to=3,number_of_steps=2, command=slider_event)
    sideslider.pack(pady=padding, padx=padding, anchor="w")

    # Create a switch for "Smoothness? (1-10):"
    def slider_event(value):
        key2 = value
        with open("config.json", "r+") as file:
            data2 = json.load(file)
            data2["smoothness"] = key2
            file.seek(0)
            json.dump(data2, file)
            file.truncate()

    sliderlabel = customtkinter.CTkLabel(aimtab, text=questions(7), fg_color="transparent")
    sliderlabel.pack(pady=padding, padx=padding, anchor="w")
    smoothslider = customtkinter.CTkSlider(aimtab, from_=1, to=10,number_of_steps=9, command=slider_event)
    smoothslider.pack(pady=padding, padx=padding, anchor="w")

    # Create a switch for "Smoothness? (1-10):"
    def fov_event(value):
        key2 = value
        with open("config.json", "r+") as file:
            data2 = json.load(file)
            data2["fov"] = key2
            file.seek(0)
            json.dump(data2, file)
            file.truncate()

    fovlabel = customtkinter.CTkLabel(aimtab, text=questions(12), fg_color="transparent")
    fovlabel.pack(pady=padding, padx=padding, anchor="w")
    fovslider = customtkinter.CTkSlider(aimtab, from_=1, to=10,number_of_steps=9, command=fov_event)
    fovslider.pack(pady=padding, padx=padding, anchor="w")


    # Create a switch for "Enter the key you want to use to activate the triggerbot:"
    trigkeyentry = customtkinter.CTkEntry(trigtab, placeholder_text=questions(8), width=290)
    trigkeyentry.pack(pady=padding, padx=padding, anchor="w")

    def trigkeyfunc():
        key2 = trigkeyentry.get()
        with open("config.json", "r+") as file:
            data2 = json.load(file)
            data2["trigkey"] = key2
            file.seek(0)
            json.dump(data2, file)
            file.truncate()
        trigkeyentry.delete(0, 'end')  # Clear the guikey entry

    trigkeybutton = customtkinter.CTkButton(trigtab, text=questions(10), command=trigkeyfunc)
    trigkeybutton.pack(pady=padding, padx=padding, anchor="w")

    # Create a switch for "Enter the key you want to use to activate the triggerbot:"
    trigdelayentry = customtkinter.CTkEntry(trigtab, placeholder_text=questions(9), width=300)
    trigdelayentry.pack(pady=padding, padx=padding, anchor="w")


    def trigdelayfunc():
        key2 = trigdelayentry.get()
        with open("config.json", "r+") as file:
            data2 = json.load(file)
            data2["trigdelay"] = key2
            file.seek(0)
            json.dump(data2, file)
            file.truncate()
        trigdelayentry.delete(0, 'end')  # Clear the guikey entry

    trigdelaybutton = customtkinter.CTkButton(trigtab, text=questions(10), command=trigdelayfunc)
    trigdelaybutton.pack(pady=padding, padx=padding, anchor="w")


    app.mainloop()


except KeyboardInterrupt:
    exit()

except Exception as e:
    print(f"An error occurred: {e}")
    # Wait for 15 seconds before closing
    time.sleep(15)