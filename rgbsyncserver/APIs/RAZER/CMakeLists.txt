cmake_minimum_required(VERSION 3.20)
project(razerAPIclient) #this is the cmake file purely for the razer api client, because it needs a requests and json library to interact with the RAZER RESTful API

set(CMAKE_CXX_STANDARD 17)

set(BUILD_SHARED_LIBS OFF) #CMake will default to static libraries with this

set(CPR_BUILD_SHARED_LIBS OFF) #builds libcpr statically
set(CPR_FORCE_USE_SYSTEM_CURL OFF) #builds curl from the source instead of the system (this is safer)

#set to C++ 11 with cpr <= 1.9.x https://github.com/libcpr/cpr#supported-releases
# set(CMAKE_CXX_STANDARD 11)

#build types reference: https://github.com/openchemistry/tomviz/blob/master/cmake/BuildType.cmake
#we just need release, note that the debug build type will add a bunch of debug only libraries that will make it give errors on other machines
set(DEFAULT_BUILD_TYPE "Release")

#if(EXISTS "${CMAKE_SOURCE_DIR}/.git")
#  set(DEFAULT_BUILD_TYPE "Debug")
#endif()
#if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
 # message(STATUS "Setting build type to '${DEFAULT_BUILD_TYPE}' as none was specified.")
  #set(CMAKE_BUILD_TYPE "${DEFAULT_BUILD_TYPE}" CACHE STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  #set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
#endif()

add_executable(razerAPIclient razerAPIclient.cpp)

if(WIN32) #puts DLLs in the same directory as the exe
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
endif()

include(FetchContent)
FetchContent_Declare(cpr GIT_REPOSITORY https://github.com/libcpr/cpr.git
                         GIT_TAG 1.11.0) # The commit hash for 1.11.x. Replace with the latest from: https://github.com/libcpr/cpr/releases
FetchContent_MakeAvailable(cpr)

include(FetchContent)
FetchContent_Declare(json URL https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz)
FetchContent_MakeAvailable(json)

target_include_directories(razerAPIclient PRIVATE ${json_SOURCE_DIR}/include)

target_link_libraries(razerAPIclient PRIVATE ws2_32)
target_link_libraries(razerAPIclient PRIVATE cpr::cpr)
target_link_libraries(razerAPIclient PRIVATE nlohmann_json::nlohmann_json)