Here is the source code and command to compile the server yourself. CMake isn't necessary as there only is one dependency (a windows library).
You will need the g++ compiler (usually from mingw: https://code.visualstudio.com/docs/cpp/config-mingw)

cd path\to\server.cpp
g++ .\rgbsyncserver\server.cpp -o .\rgbsyncserver\server.exe -lws2_32