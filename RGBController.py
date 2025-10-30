from tkinter import *
from tkinter import ttk
from tkinter import colorchooser

import pystray
from PIL import Image

import subprocess
import sys
import os

def resource_path(relative_path):
    '''
    A useful function for absolute paths for both release and debug versions, see below:
    #https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
    '''
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

WINDOW_HEIGHT= 600
WINDOW_WIDTH = 550

APPLICATION_NAME = "RGB Controller"
MAX_PROFILES = 10
SUPPORTED_DEVICES = ['All', 'Keyboard', 'Mouse', 'Memory Module', 'Led Hub', 'Cooler', 'Headset'] #note that these correspond to the device_id numbers, e.x. keyboard = 01
PATTERN_LIST = ['static', 'pulse', 'rainbowpulse', 'rainbowcycle', 'randomstrobe', 'fire']
SPEED_VALUES = ['Slow', 'Medium', 'Fast']

rgbProcesses = [] #contains all created subprocesses that are currently affecting rgb devices, note the current implementation only calls for one, server.exe, which spawns api subprocesses
current_selected_pattern = 'static'
current_selected_device = 'All'

class RGBController(Tk):
    '''
    Custom Tkinter instance to support system tray functionality, with our app icons.
    '''
    def __init__(self):
        super().__init__()
        self.title(APPLICATION_NAME)
        self.protocol('WM_DELETE_WINDOW', self.minimize_to_tray) #instead of closing, goes to tray
        self.iconbitmap(resource_path("./resources/app.ico"))
        self.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))
    
    def minimize_to_tray(self):
        self.withdraw()
        image = Image.open(resource_path("./resources/app.png"))
        menu = (pystray.MenuItem('Quit',  self.quit_window), 
                pystray.MenuItem('Show',self.show_window)) #tray options
        icon = pystray.Icon("name", image, APPLICATION_NAME, menu)
        icon.run()

    def quit_window(self, icon): #tray option to stop running
        icon.stop()
        close_app(self) #closes subprocesses and graphs

    def show_window(self, icon): #tray option to return back to window
        icon.stop()
        self.after(0,self.deiconify)

class DevicePattern():
    '''
    Object that holds pattern information for each device type
    '''
    def __init__(self, device_id='0', r='255', g='255', b='255', a='255', speed=1, pattern='static'):
        self.device_id = device_id
        self.r = r
        self.g = g
        self.b = b
        self.a = a
        self.speed = speed 
        self.pattern = pattern
        self.valid = False

    def setValid(self, valid):
        self.valid = valid

#initialize our device patterns for each device, note that they start off as invalid
device_patterns = [DevicePattern() for x in range(0, len(SUPPORTED_DEVICES))]
for index, device in enumerate(device_patterns):
    device.device_id = str(index)

def handle_rgb_processes():
    '''
    This process properly closes the pattern-generating RGB subprocesses for each of our currently-supported APIs.
    Sends a signal to each one, then wipes the processes list.
    Note: this returns the rgb devices to whatever state they were in prior to opening the program, so any patterns set by default or by another program will turn back on.
    '''
    global rgbProcesses
    if rgbProcesses:
        for process in rgbProcesses:
            process.kill()

    rgbProcesses = [] # empty our processes as none are running anymore

def close_app(win):
    '''
    This function is a called when the program is closed. 
    Properly terminates and removes all pattern-creating subprocesses and graphs.
    '''
    handle_rgb_processes()
    win.destroy()
    win.quit()

def open_rgb_service(args):
    '''
    Assuming RGBA values and pattern are valid, starts the pattern-creating subprocess for each API we support and adds it to our subprocess list.
    Does nothing if supplied parameters are invalid.
    Also terminates and removes the processes for any previous effect properly, so it does not conflict with our new effect.
    '''

    global rgbProcesses
    
    #close other effects so they don't conflict with our new one
    handle_rgb_processes()

    rgbProcesses.append(subprocess.Popen(resource_path("./rgbsyncserver/server.exe") + " " + " ".join(args),
                                          stdout=subprocess.PIPE, shell=False, cwd=resource_path('./rgbsyncserver'),creationflags=subprocess.CREATE_NO_WINDOW))

    #https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing this is why the pyinstaller --onefile option does not work. use the default configuration (--onedir) instead

def save_profile(profile_id):
    '''
    Saves pattern data for all devices under profile_id.
    Writes these settings to a file in the user's home directory -> /RGBController/rgbprofile_(profile_id)
    '''
    home_path = os.path.expanduser("~")
    path = home_path + "/RGBController"
    #recursively create the directory structure if it can't be found
    os.makedirs(path, exist_ok=True)

    file = open(path + "/rgbprofile_" + str(profile_id), "w")
    #now write out all the patterns for each device under this profile
    for device in device_patterns:
        if device.valid:
            file.write(str(device.device_id) + " " +  device.r + " " + device.g + " " + device.b + " " + device.a + " " + device.speed + " " + device.pattern + "\n")
    file.close()

def load_profile(profile_id, device_data):
    '''
    Loads pattern data for all devices under profile_id, and then starts up the rgb server to start displaying patterns.
    Finds these settings from a file in the user's home directory -> /RGBController/rgbprofile_(profile_id)
    Also changes the settings file in the user's home directory -> /RGBController/rgbprofile_settings to accomodate the user's new last loaded profile.
    Does not load profiles that do not exist.
    Edits device_data to be equal to the device patterns found inside the profile file, and sets the active patterns to valid.
    '''
    global device_patterns

    home_path = os.path.expanduser("~")
    path = home_path + "/RGBController"
    os.makedirs(path, exist_ok=True)

    settings_path = path + "/rgbprofile_settings"
    found_last_profile = False

    #start by setting the new last loaded profile for the user
    if os.path.exists(settings_path):
        with open(settings_path, "r") as file:
            data = file.readlines()
            for index in range(0, len(data)):
                line_list = data[index].split()
                if line_list[0] == 'last_loaded_profile': 
                    data[index] = 'last_loaded_profile ' + str(profile_id)
                    found_last_profile = True
                    break
        if found_last_profile:
            with open(settings_path, 'w') as file:
                file.writelines(data)
    else:
        with open(settings_path, "w") as file:
            file.writelines('last_loaded_profile ' + str(profile_id))

    #now load the device data from the profile file
    profile_path = path + "/rgbprofile_" + str(profile_id)
    if os.path.exists(profile_path):

        for stringvar in device_data:
            stringvar.set("Pattern: None selected yet")

        for devicepattern in device_patterns:
            devicepattern.setValid(False)

        with open(profile_path, 'r') as file:
            values = []
            for line in file:
                line_values = line.split()
                device_num = int(line_values[0])
                if line_values[1] == '0' and line_values[2] == '0' and line_values[3] == '0' and line_values[6] == 'static':
                    device_data[device_num].set("Pattern: OFF")
                else:
                    device_data[device_num].set(
                                                "Pattern: " + line_values[6]
                                                + ", R = " + line_values[1]
                                                + ", G = " + line_values[2]
                                                + ", B = " + line_values[3]
                                                + ", A = " + line_values[4]
                                                + ", Speed = " + SPEED_VALUES[int(line_values[5])]
                                                )
                device_patterns[device_num].setValid(True)
                device_patterns[device_num].r = line_values[1]
                device_patterns[device_num].g = line_values[2]
                device_patterns[device_num].b = line_values[3]
                device_patterns[device_num].a = line_values[4]
                device_patterns[device_num].speed = line_values[5]
                device_patterns[device_num].pattern = line_values[6]

                if line_values[0] == '0': #this is the 'All' identifier, so we just ignore any other patterns and apply this one to all devices
                    values = line_values
                    break
                else:
                    values.extend(line_values)
            open_rgb_service(values)

def read_profile(profile_id):
    '''
    Reads pattern data for all devices under profile_id, for displaying the settings within the GUI.
    Finds these settings from a file in the user's home directory -> /RGBController/rgbprofile_(profile_id)
    '''
    home_path = os.path.expanduser("~")
    path = home_path + "/RGBController"
    profile_path = path + "/rgbprofile_" + str(profile_id)
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as file:
            values = []    
            first_line = True
            for line in file:
                line_list = line.split()
                if first_line:
                    first_line = False
                else:
                    values.append("\n")
                values.append("Device: " + SUPPORTED_DEVICES[int(line_list[0])])
                if line_list[1] == '0' and line_list[2] == '0' and line_list[3] == '0' and line_list[6] == 'static':
                    values.append(", Pattern = OFF")
                else:
                    values.append(", R = " + line_list[1])
                    values.append(", G = " + line_list[2])
                    values.append(", B = " + line_list[3])
                    values.append(", A = " + line_list[4])
                    values.append(", Speed = " + SPEED_VALUES[int(line_list[5])])
                    values.append(", Pattern = " + line_list[6])
                if line_list[0] == '0':
                    break
            return " ".join(values)
        
def load_profile_on_startup(profile_tabs, device_data):
    '''
    Loads pattern data for all devices under the last loaded profile_id, if it exists within the settings file -> /RGBController/rgbprofile_settings
    '''
    home_path = os.path.expanduser("~")
    path = home_path + "/RGBController"
    settings_path = path + "/rgbprofile_settings"
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as file:
            for line in file:
                line_list = line.split()
                if line_list[0] == 'last_loaded_profile' and line_list[1] != '-1':
                    profile_tabs.select(int(line_list[1]) - 1)
                    load_profile(int(line_list[1]), device_data)
                    return

def init_gui(win):
    '''
    Initializes all widgets required for the GUI, with their functionality.
    '''
    global current_selected_pattern

    #title, colour selection instructions and picker
    msg = Message(win, width=WINDOW_WIDTH, text="Change Your RGB Here!", justify=CENTER)
    msg.config(font=('times', 18, 'bold'))
    msg.pack(pady=5)

    msg = Message(win, width=WINDOW_WIDTH, text="Select a colour, adjust your brightness and speed,\n select your device, then click a pattern!\nRepeat this for all your devices, and then you can save your configuration to a profile.",
                   justify=CENTER, highlightbackground="black", highlightthickness=3)
    msg.config(font=('times', 12))
    msg.pack(pady=5)

    #these are the values of the rgba in the gui
    colours = ['255', '255', '255' ,'255']
    
    def pick_color():
        '''
        Opens the windows color picker, and edits the colours variables to respond to the chosen rgb. Also changes the square color icon to match the selected color.
        '''
        color = colorchooser.askcolor()[1]
        if color:
            color_str = color[1:]
            colours[0] = str(int(color_str[0:2], 16))
            colours[1] = str(int(color_str[2:4], 16))
            colours[2] = str(int(color_str[4:6], 16))
            color_icon_label.config(background=color)  #changes the displayed colour

    colourFrame = Frame(win)
    colourFrame.pack()

    #button to open the color dialog
    color_button = Button(colourFrame, text="Click to select a colour !", font=("Helvetica", '16', "bold") , command=pick_color)
    color_button.pack(side='top')

    colourSubFrame = Frame(colourFrame)
    colourSubFrame.pack(side='top')

    #display the selected color in a box
    color_label = Label(colourSubFrame, text="YOUR SELECTED COLOUR:", font=("times", 14, 'bold'))
    color_label.pack(side='left', padx=5, pady=10)

    color_icon_label = Label(colourSubFrame, text="     ", highlightbackground="black", highlightthickness=3)
    color_icon_label.pack(side='left', padx=5, pady=10)

    #brightness label and slider
    brightnessFrame = Frame(win)
    brightnessFrame.pack()

    brightnessSubFrame = Frame(brightnessFrame)
    brightnessSubFrame.pack(side='left')

    brightness_label = Label(brightnessSubFrame, text="Select your brightness level: ", font=("times", 12))
    brightness_label.pack(side='top', pady=5)

    w = Scale(brightnessFrame, from_=0, to=255, orient=HORIZONTAL, length=150)
    w.set(255)
    w.pack(side='left')

    #speed label and slider
    speedFrame = Frame(win)
    speedFrame.pack()

    label = Label(speedFrame, text="Select your effect speed:", font=("times", 12))
    label.pack(side='left', pady=5)

    speedSubFrame = Frame(speedFrame)
    speedSubFrame.pack(side='left', padx=15)

    speedValuesFrame = Frame(speedSubFrame)
    speedValuesFrame.pack(side='top')
    for value in ["Slow", "Medium", "Fast"]: #this is needed to replace the numbers with words
        valueLabel = Label(speedValuesFrame, text=value, width=6, anchor='center', font=("times", 10))
        valueLabel.pack(side='left',expand=True)

    s = Scale(speedSubFrame, from_=0, to=2, orient=HORIZONTAL, showvalue=0, length=100)
    s.set(1)
    s.pack(side='top')

    #start of device tabs, which are used to correspond with the chosen pattern and colors for each device
    device_tabs = ttk.Notebook(win, width=WINDOW_WIDTH)
    #device data is just a string for each device tab which display pattern information
    device_data = [StringVar() for i in range(0,len(SUPPORTED_DEVICES))]

    #initialize the device tabs and their information
    for index, device_type in enumerate(SUPPORTED_DEVICES):
        device_frame = Frame(device_tabs)
        device_label = Label(device_frame, textvariable=device_data[index])
        device_label.pack()
        device_tabs.add(device_frame, text=device_type)
        device_tabs.pack(expand=1)
        device_data[index].set("Pattern: None selected yet")

    def apply_effect_and_update(button):
        '''
        Function for clicking pattern buttons. Edits the currently selected device_pattern (selected via the devices tab in the GUI) to match what has been selected
        from the different attributes in the GUI, and opens the rgb server to display it. Note that this only applies effects to the selected device (singular) at a time.
        Also changes the device_data (text for the device tab) to reflect the selected pattern, and updates the currently selected pattern.
        '''
        #TODO: fix this to have less boilerplate
        global current_selected_pattern
        if button['text'] == 'RGB OFF': #RGB being OFF just means a static black pattern with zero brightness
            current_selected_pattern = 'static'
            device_identifier = str(device_tabs.index(device_tabs.select()))
            open_rgb_service([device_identifier, '0', '0', '0', '0', '0', 'static'])
            device_data[device_tabs.index(device_tabs.select())].set("Pattern: OFF") 
            device_patterns[device_tabs.index(device_tabs.select())].r = '0'
            device_patterns[device_tabs.index(device_tabs.select())].g = '0'
            device_patterns[device_tabs.index(device_tabs.select())].b = '0'
            device_patterns[device_tabs.index(device_tabs.select())].a = '0'
            device_patterns[device_tabs.index(device_tabs.select())].speed = '0'
            device_patterns[device_tabs.index(device_tabs.select())].pattern = 'static'
            device_patterns[device_tabs.index(device_tabs.select())].valid = True
            return

        current_selected_pattern = button['text']
        device_identifier = str(device_tabs.index(device_tabs.select()))
        open_rgb_service([device_identifier, colours[0], colours[1], colours[2], str(w.get()), str(s.get()), button['text']])
        device_data[device_tabs.index(device_tabs.select())].set("Pattern: " + button['text'] +
                                                                ", R = " + colours[0] +
                                                                ", G = " + colours[1] +
                                                                ", B = " + colours[2] +
                                                                ", A = " + str(w.get()) +
                                                                ", Speed = " + SPEED_VALUES[s.get()])
        device_patterns[device_tabs.index(device_tabs.select())].r = colours[0]
        device_patterns[device_tabs.index(device_tabs.select())].g = colours[1]
        device_patterns[device_tabs.index(device_tabs.select())].b = colours[2]
        device_patterns[device_tabs.index(device_tabs.select())].a = str(w.get())
        device_patterns[device_tabs.index(device_tabs.select())].speed = str(s.get())
        device_patterns[device_tabs.index(device_tabs.select())].pattern = current_selected_pattern
        device_patterns[device_tabs.index(device_tabs.select())].valid = True

    rgbOptionsFrame = Frame(win)
    rgbOptionsFrame.pack()
    pattern_buttons = []

    #now we render the pattern buttons
    for pattern in PATTERN_LIST:
        patternButton = Button(master=rgbOptionsFrame, text=pattern)
        patternButton.configure(command=lambda button=patternButton: apply_effect_and_update(button))
        patternButton.pack(side='left', padx=5, pady=5)
        pattern_buttons.append(patternButton)

    rgbFrame = Frame(win)
    rgbFrame.pack()

    #this button applies a completely dark effect, akin to the LEDs being turned off
    rgbOFFButton = Button(master=rgbFrame, text="RGB OFF")
    rgbOFFButton.configure(command= lambda button=rgbOFFButton: apply_effect_and_update(button))
    rgbOFFButton.pack(side=LEFT, padx=5, pady=5)

    #the RGB STOP button destroys all pattern displaying processes, returning devices to system defaults
    rgbStopButton = Button(master=rgbFrame, text="No Pattern", command=lambda: (handle_rgb_processes(),
                                                                                          device_data[device_tabs.index(device_tabs.select())].set("Pattern: None selected yet"),
                                                                                          device_patterns[device_tabs.index(device_tabs.select())].setValid(False)
                                                                                          ))
    rgbStopButton.pack(side=RIGHT, padx=5, pady=5)

    #another grouping of tabs, this time for effect profiles
    profile_tabs = ttk.Notebook(win)
    profile_data = [StringVar() for i in range(0,MAX_PROFILES)]

    for index, profile in enumerate(profile_data):
        profile_frame = Frame(profile_tabs)
        profile_label = Label(profile_frame, textvariable=profile_data[index])
        profile_label.pack()
        profile_tabs.add(profile_frame, text="Profile " + str(index + 1))
        profile_tabs.pack(expand=1)
        profile.set(read_profile(index + 1))
    profile_tabs.pack(expand=1)
    
    profilesFrame = Frame(win)
    profilesFrame.pack()

    #buttons for saving and loading profiles, each with complete functionality

    saveProfileButton = Button(profilesFrame, text="Save to this profile", command= lambda: (save_profile(profile_tabs.index(profile_tabs.select()) + 1),
                                                                                    profile_data[profile_tabs.index(profile_tabs.select())].set(read_profile(profile_tabs.index(profile_tabs.select()) + 1))
                                                                                    )
                                                                                        )
    saveProfileButton.pack(side='left', padx=5, pady=5)

    loadProfileButton = Button(profilesFrame, text="Load profile", command= lambda: load_profile(profile_tabs.index(profile_tabs.select()) + 1, device_data))
    loadProfileButton.pack(side='left', padx=5, pady=5)

    #a button that explains what the application does

    def open_help_window():
        help_window = Toplevel(win)
        help_window.title("FAQ")
        help_window.iconbitmap(resource_path("./resources/app.ico"))
        text = Label(help_window,
                     text="What is this program?\n" \
                        "This program centralizes the different RGB device brand APIs on your computer to synchronize patterns across your devices.\n\n" \
                        "What devices are supported?\n" \
                        "Currently we have support for Corsair and RAZER products that are rgb-programmable.\n\n" \
                        "My device isn't connecting/lighting up!\n" \
                        "Be sure to have the corresponding device's software (e.x. Synapse for a RAZER device) installed and running at the time of loading your lighting pattern.\n" \
                        "Check your product to see if it is rgb-programmable (e.x. the RAZER Blackwidow's 1st version only has green lights).\n" \
                        "If the product is new, once you have installed the brand's software for the device, set it up within that software and restart your computer.\n\n"
                        "Windows Defender/My antivirus is flagging this program!\n" \
                        "This program's executable was created using pyinstaller (https://pyinstaller.org/en/stable/). Because of bad actors, sometimes real programs get flagged as well.\n" \
                        "If you don't trust this program, all the source code is available, along with ways to generate the executable by yourself on your own computer, which will likely fix the issue.\n\n" \
                        "Certain patterns/devices don't work properly when my computer sleeps/when I log out!\n" \
                        "This is because certain device APIs (such as Corsair's iCUE) do not work when the user is logged out. If patterns seem to break upon logging in, be sure to run this\n" \
                        "program with Administrator privileges, so it can detect the login events from Windows and restart the connection to API so your pattern can resume after logging in.\n\n" \
                        "How do I make my patterns start up when my computer turns on?\n" \
                        "Before this program turns on and connects to your devices, there isn't a way to set your patterns before your OS starts up. This is likely the case for most brands\n" \
                        "such as RAZER devices which need Synapse to be running (requiring the OS) to display set patterns, even if those patterns are set up in Synapse themselves.\n" \
                        "However, you can set the program to start up automatically on Window Startup; see the startup folder in the RGBController directory for instructions.")
        text.pack()

    helpButton = Button(profilesFrame, text="Need Help?", command=open_help_window)
    helpButton.pack(side='left', padx=5, pady=5)

    #finally, load the last loaded profile (if possible)
    load_profile_on_startup(profile_tabs, device_data)

if __name__ == "__main__":
    win = RGBController()
    #the following requires all Tk widgets be replaced by ttk widgets
    #style = ttk.Style()
    #style.theme_use('alt')
    init_gui(win)
    win.mainloop()