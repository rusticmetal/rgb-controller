# Cross-API Device RGB Controller for Windows

This application provides a simple interface to changing the patterns and colours of the LEDs of devices connected to your computer. You can set individual pc components, like keyboards, mice, headsets, RAM modules, and coolers to the same (or different) supported LED patterns, with your own custom colours. If you need synchronized patterns for your devices' LEDs that are split between multiple device brands and setting it up in multiple programs is a hassle, this application may be useful. 

It works to sync your devices by establishing connections to all your devices' manufacturer's softwares that are running on the computer (like Corsair's iCUE or RAZER's Synapse) automatically, and setting up a local synchronized "server" process on your computer that operates on a universal timer giving out synced colour data to all the device APIs on your system, which in turn updates the colours of your devices at the same time.

Currently only Corsair and Razer devices are supported.

# Dependencies

Dependencies to run this program with all functionality enabled (These are needed to interface with the devices via the manufacturer's APIs to change their RGB values):

Corsair's iCUE Software: https://www.corsair.com/ca/en/s/icue
(if you have corsair devices, must be running)

Razer's Synapse Software: https://www.razer.com/ca-en/synapse
(if you have razer devices, must be running)

Microsoft's C++ Redistributable DLLs: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170
(if the application gives you missing DLL errors)

# Startup Functionality

If you want to set the program up to start when you start your computer, see the /startup/ folder and follow the instructions. Note that for it to work successfully on startup you need to set the manufacturer's software (iCUE/Synapse) to be active on startup. Make sure to set the timeout to a value in seconds that is longer than it takes for your computer to
load those applications.

# To build it yourself

If the executable doesn't work or is flagged by an antivirus (or you don't trust it), the source code and its dependencies with their sources are also included,
with trusted sites to obtain them (see the README.txt file in each directory). 

The files you see in the iCUESDK folder (other than corsairAPIclient.cpp) are directly from Corsair's SDK: 

https://github.com/CorsairOfficial/cue-sdk

https://github.com/CorsairOfficial/cue-sdk/releases (in the zip file, /redist/ folder)

These two libraries were used to create the RAZER API client: 

https://github.com/libcpr/cpr

https://github.com/nlohmann/json

You need to have g++ (the C++ GNU compiler), git, CMake, python, and the python modules already installed (along with an internet connection to fetch some libraries on github), 
so you can generate all required files and the executable with the included make.ps1 file in this directory.
The build folder and .spec files are generated but are not needed for runtime, you can delete them after program compilation.

git: https://git-scm.com/downloads/win, 

CMake: https://cmake.org/

mingw: https://code.visualstudio.com/docs/cpp/config-mingw (though other compilers definitely work as well, 
they won't work with the make.ps1 script, so you would have to compile it manually without the script with other compilers): 

python: https://www.python.org/downloads/

Once you have all the dependencies to build the executable, run the make.ps1 file and it will generate the application.
You can also run each command one by one in order in the make.ps1 if that is easier, just open your command prompt and enter the commands within the quotations (make sure the path is correct though).

By doing this you can look at the source code, compile it and package it yourself. This may also prevent your computer from falsely flagging it as dangerous.

The created application should be /RGBController/RGBController.exe.

# Known Issues

If windows defender or another antivirus falsely sees the program or its subprocesses as malicious, try generating/regenerating the program with the above method, and
running make.ps1 more than once can solve some of these issues.

If you have set up the program to autostart upon your first login and are experiencing issues, try:
1) disabling windows fast startup

If waking up your computer results in unexpected pattern behaviour, try:
1) running the program with administrator privileges
2) disabling wakeup from sleep for that specific device in device manager
3) Option #2 in /startup/README.md

If the installing the python modules gives errors, try doing "pip install -r requirements.txt" by itself in a terminal and then manually installing the modules that give errors separately.

# Current Bugs:

- [ ] Settings pattern speed to high can overload(?) certain RAZER devices, causing them to update their pattern slower than other devices

# TODO:

- [ ] pulse and rainbow cycle are too slow
- [ ] add the rest of the device types to the corsair API client
- [ ] styling/themes
- [ ] remove widgets when not in use/when program is in system tray, to save memory
- [ ] replace sockets with named pipes ? (have to be careful about waking from sleep functioning properly though)
- [ ] organize the classes in their own files
- [ ] use os.path.join for paths + use appdirs module
- [ ] use a json for the pattern data instead of txt files
- [ ] implement per-LED patterns (requires tweaking for each individual API), i.e. waves
    -> this may require reworking the data structures (might need a map of colours), but we can just send the struct as data over the socket instead of just a singular colour. We will need to re-organize where the structs are defined so that the clients can use them because right now they don't need to