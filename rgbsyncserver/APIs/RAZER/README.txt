Here is the source code and steps to compile the razer api client yourself.

To compile this program you will need git (to fetch some dependencies): https://git-scm.com/downloads/win, and CMake to link them: https://cmake.org/.

The dependencies (which can be viewed from the CMakeLists.txt file) are https://github.com/libcpr/cpr, https://github.com/nlohmann/json, and lws2_32 which is a library that comes with windows.

To generate this program separately (without the use of make.ps1), we can make a temporary build directory here.

cd path/to/razerAPIclient.cpp
mkdir build
cd build
cmake ..
cmake --build

The program will be at ./build/Debug/razerAPIclient.exe