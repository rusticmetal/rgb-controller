#run this to automatically compile the the subprocess binaries and then generate the executable
#note that since the project uses regular gcc, CMake AND pyinstaller, a script like this was needed (and since this is a windows program, its powershell)

#the g++ compiler, git, cmake, python and the pyinstaller module (as well as any other required python modules) are needed to generate using this method
#sometimes this script hangs depending on your terminal or if you tab out, if this happens just close it and run it again

#g++/mingw: https://code.visualstudio.com/docs/cpp/config-mingw
#CMake: https://cmake.org/
#Git: https://git-scm.com/downloads/win
#Python: https://www.python.org/downloads/
#PyInstaller: https://pyinstaller.org/en/stable/
#psytray: https://pypi.org/project/pystray/

#installs the python modules needed for compilation, note that this is prone to errors due to the nature of there existing several versions of different libraries
#if the below command gives errors, try doing "pip install -r requirements.txt" by itself in a terminal and then manually installing the modules that give errors separately
Start-Process -FilePath "cmd.exe"  -ArgumentList '/c "pip install -r requirements.txt"' -wait

#compiles the corsair API client with g++, needs a windows library and the corsair library
Start-Process -FilePath "cmd.exe"  -ArgumentList '/c "g++ .\rgbsyncserver\APIs\iCUESDK\corsairAPIclient.cpp -o .\rgbsyncserver\APIs\iCUESDK\corsairAPIclient.exe -static -lws2_32 -I .\rgbsyncserver\APIs\iCUESDK\include -L .\lib .\rgbsyncserver\APIs\iCUESDK\iCUESDK.x64_2019.lib"' -wait

#razer API client, builds it first with CMake (it needs two different dependencies to send and parse the restful API requests)
Start-Process -FilePath "cmd.exe"  -ArgumentList '/c "cmake -S .\rgbsyncserver\APIs\RAZER -B .\build\RAZER\razerAPIclient"' -wait
Start-Process -FilePath "cmd.exe"  -ArgumentList '/c "cmake --build .\build\RAZER\razerAPIclient --config Release"' -wait

#then copies only the needed file to run the executable
Copy-Item -Path ".\build\RAZER\razerAPIclient\Release\razerAPIclient.exe" -Destination ".\rgbsyncserver\APIs\RAZER\"

#the main rgb syncing server, needs two windows libraries
Start-Process -FilePath "cmd.exe"  -ArgumentList '/c "g++ .\rgbsyncserver\server.cpp -o .\rgbsyncserver\server.exe -static -lws2_32 -lwevtapi"' -wait

#final executable
Start-Process -FilePath "cmd.exe" -ArgumentList '/c "pyinstaller RGBController.py --distpath . --icon=./resources/app.ico --add-binary="rgbsyncserver/server.exe":"rgbsyncserver" --add-binary="rgbsyncserver/APIs/iCUESDK/corsairAPIclient.exe":"rgbsyncserver/APIs/iCUESDK/" --add-binary="rgbsyncserver/APIs/RAZER/razerAPIclient.exe":"rgbsyncserver/APIs/RAZER/" --add-data="resources":"resources" --onefile --noconsole --windowed --clean --noconfirm"' -wait