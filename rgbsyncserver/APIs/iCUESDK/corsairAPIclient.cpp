#include <winsock2.h>
#include <windows.h>
#include <iostream>
#include "iCUESDK.h"
#include <map>
#include <chrono>

//this can also be done with a g++ compiler flag usually, which is what we do in the make file
#pragma comment(lib, "ws2_32.lib")  //links the winsock2 library

//use this to compile by itself in this directory
//g++ corsairAPIclient.cpp -o corsairAPIclient.exe -lws2_32 -I .\include -L .\lib .\iCUESDK.x64_2019.lib

//official corsair api here https://github.com/CorsairOfficial/cue-sdk
//official documentation here https://corsairofficial.github.io/cue-sdk/
//also check out the header files for the api's implementation and functionality, all of these were grabbed from the above repositories

const int PORT = 50025;

std::map<int, CorsairDeviceType> device_map = { //this is used for identifying the device(s) to use when receiving pattern data
    { 0, CDT_All},
    { 1, CDT_Keyboard},
    { 2, CDT_Mouse },
    { 3, CDT_MemoryModule},
    { 4, CDT_LedController}, 
    { 5, CDT_Cooler},
    { 6, CDT_Headset}
};

void onStateChanged (void *context, const CorsairSessionStateChanged *eventData) {
    //called when the api changes states (not connected/connecting/connected)
    //not necessary to be implemented, this is just to compile nicely

    //std::cout << "Corsair State: " << eventData->state << std::endl;
    return;
}

int connect_icue() {
    /*
    Attempts to connect and establish state with the iCUE service, if it is installed and currently running on the system.
    Retries every 300ms, up to 10 times (retries for 3 seconds).
    Returns 0 if successful, 1 if not.
    */
    int MAX_RETRIES = 10;
    int retries = 0;

    while (retries < MAX_RETRIES) { //try to reconnect (this is necessary, sometimes the takes a second)
        void * context = NULL; //context not necessary for changing rgb

        //connect to the api and grab the details, a server version of (0, 0, 0) represents failure to connect
        CorsairConnect(onStateChanged, context);

        CorsairSessionDetails details;
        CorsairGetSessionDetails(&details);
    
        if (details.serverVersion.major != 0) { //iCUE has connected
            //std::cout << "ICUE CONNECTED" << std::endl;
            return 0;
        }

        Sleep(300);

        retries += 1;

        if (retries == MAX_RETRIES) { //iCUE could not connect, either do to an error or the fact that it isn't currently installed
            //std::cout << "ICUE DID NOT CONNECT" << std::endl;
            return 1;
        }
    }
    return 1;
}

void async_callback (void *context, CorsairError error) {
    //used as a callback for asynchronous setting of RGB through the used of a buffer, not currently implmented due to using a synchronous implementation
    return;
}

int main(int argc, char *argv[]) {
    /*
    The main process for delivering RGB patterns to Corsair devices.
    Handles establishing a connection to the iCUE SDK and setting up a client socket connection to the main server process.
    Closes early after 2 hours to prevent iCUE runon bug, though the main server process will restart another instance and keep relaying patterns.
    */
    int MAX_RETRIES = 10;
    int retries = 0;

    if (connect_icue() != 0) {
        return 1;
    }

    WSADATA wsaData;
    SOCKET recvSocket;
    sockaddr_in serverAddr;

    //here we initialize the winsock instance, similar to the winsock client code: https://learn.microsoft.com/en-us/windows/win32/winsock/complete-client-code
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed with error: " << WSAGetLastError() << "\n";
        return 1;
    }

    //this is our socket
    recvSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (recvSocket == INVALID_SOCKET) {
        //std::cerr << "Socket creation failed with error: " << WSAGetLastError() << "\n";
        WSACleanup();
        return 1;
    }

    const char* address = "127.0.0.1";
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(PORT);
    serverAddr.sin_addr.s_addr = inet_addr(address);

    //now we connect to the main server process
    if (int((connect(recvSocket, (SOCKADDR*)&serverAddr, sizeof(serverAddr)))) == int(SOCKET_ERROR)) {
        //std::cerr << "Connection failed with error: " << WSAGetLastError() << "\n";
        closesocket(recvSocket);
        WSACleanup();
        return 1;
    }

    char recvBuf[15];
    int bytesReceived;

    CorsairSetLayerPriority(255); //so other applications do not override our rgb configuration

    //we need to time the connections because of an internal bug within the iCUE SDK, it halts programs that run on too long
    std::chrono::steady_clock::time_point lastReconnect = std::chrono::steady_clock::now();

    while (true) { //now we continuously try to receive pattern data from the server process and display it
        try {

            //this is needed to determine if the program has gone on too long, which will result in unspecified behaviour from the iCUE SDK
            auto now = std::chrono::steady_clock::now();
            if (std::chrono::duration_cast<std::chrono::minutes>(now - lastReconnect).count() >= 120) {
                //std::cout << "2 HOURS REACHED, CORSAIR CLOSING AND RESTARTING" << std::endl;

                closesocket(recvSocket);
                WSACleanup();
                //std::cout << "CORSAIR CLOSING" << std::endl;
                return 1;
            }

            //std::cout << "Waiting for input" << std::endl;
            bytesReceived = recv(recvSocket, recvBuf, sizeof(recvBuf) - 1, 0);   

            if (bytesReceived > 0) {
                recvBuf[bytesReceived] = '\0'; //null terminate the pattern data
                //std::cerr << "Received: " << recvBuf << "\n";
            } else if (bytesReceived == 0) {
                //std::cerr << "Connection closed by server.\n";
                break;
            } else {
                //std::cerr << "recv failed with error: " << WSAGetLastError() << "\n";
                break;
            }
            
            //see server.cpp for the proper data packet format
            char charbuffer[12];
            strncpy(charbuffer, recvBuf, 2);
            int device_num = atoi(charbuffer);  
            strncpy(charbuffer, recvBuf + 2, 3);
            int r = atoi(charbuffer);  
            strncpy(charbuffer, recvBuf + 5, 3);
            int g = atoi(charbuffer);
            strncpy(charbuffer, recvBuf + 8, 3);
            int b = atoi(charbuffer);
            strncpy(charbuffer, recvBuf + 11, 3);
            int a = atoi(charbuffer);

            //create filter to get devices, maybe change the programs input to include an option for specifying device type
            CorsairDeviceFilter filter;
            filter.deviceTypeMask = (CorsairDeviceType) device_map[device_num];

            //array of discovered devices
            CorsairDeviceInfo devices[CORSAIR_DEVICE_COUNT_MAX];
            int size;

            //populations device list, NOTE: if at any point we receive CE_ERROR (or anything that isn't CE_SUCCESS) we should exit
            if (CorsairGetDevices(&filter, CORSAIR_DEVICE_COUNT_MAX, devices, &size) != CE_Success) {
                closesocket(recvSocket);
                WSACleanup();
                return 1;
            }

            //std::cout << "Got devices: " << devices << std::endl;

            for (int device_index=0; device_index < size; device_index++) {
                //std::cout << "Now changing RGB of " << devices[device_index].model << std::endl;
            
                int led_amounts;
                struct CorsairLedColor colors[CORSAIR_DEVICE_LEDCOUNT_MAX];
                struct CorsairLedPosition positions[CORSAIR_DEVICE_LEDCOUNT_MAX];

                //this gives us the Luids to set the new colors
                if (CorsairGetLedPositions(devices[device_index].id, devices[device_index].ledCount, positions, &led_amounts) != CE_Success) {
                    closesocket(recvSocket);
                    WSACleanup();
                    return 1;
                }

                //std::cout << "Positions have been obtained: " << positions << std::endl;

                //set the colors for each led
                for (int led_num=0; led_num < led_amounts; led_num++) {
                    colors[led_num].id = (CorsairLedLuid) positions[led_num].id;
                    colors[led_num].r = (unsigned char) r;
                    colors[led_num].g = (unsigned char) g;
                    colors[led_num].b = (unsigned char) b;
                    colors[led_num].a = (unsigned char) a;
                }

                //this sends our new rgb configurations to the api
                if (CorsairSetLedColors(devices[device_index].id, devices[device_index].ledCount, colors) != CE_Success) {
                    closesocket(recvSocket);
                    WSACleanup();
                    return 1;
                }

                //std::cout << "Colours set" << std::endl;
            }

            } catch (...) { //this catches errors as well as termination signals from the main server process
                closesocket(recvSocket);
                WSACleanup();
                exit(0);
        }
    }

    //WARNING: DO NOT CALL DISCONNECT IF WE RECEIVE CORSAIRERROR != 0. IT HALTS THE PROGRAM
    CorsairDisconnect(); //disconnects from api (relinquishes exclusive light control, however)
    closesocket(recvSocket);
    WSACleanup();

    return 0;
}