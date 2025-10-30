Here is the source code and steps to compile the corsair api client yourself.

You will need a C++ compiler if you wish to compile this program (which can run on its own with the server, it just changes your corsair devices' RGBs). Here your can install mingw for windows:

https://code.visualstudio.com/docs/cpp/config-mingw

And to compile the program, with the API's dll and lib dependencies:

cd /path/to/corsairAPIclient.cpp
g++ corsairAPIclient.cpp -o corsairAPIclient.exe -I .\include -L .\lib .\iCUESDK.x64_2019.lib 

The other files in this folder are the dependencies for interacting with corsair's API, written by and owned corsair themselves, which you can see here (and re-download, if you want):
https://github.com/CorsairOfficial/cue-sdk
https://github.com/CorsairOfficial/cue-sdk/releases (in the zip file, /redist/ folder)