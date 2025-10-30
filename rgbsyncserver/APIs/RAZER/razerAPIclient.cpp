#include <winsock2.h>
#include <windows.h>
#include <iostream>
#include <string>
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>
#include <vector>
#include <map>

//changing RAZER device RGB's is done via the RAZER Synapse RESTful API here: https://assets.razerzone.com/dev_portal/REST/html/index.html 

const int PORT = 50025;

cpr::Url RAZER_API_URL = "http://localhost:54235/razer/chromasdk"; //this is the url of the API responsible for handling device pattern requests

std::map<int, std::string> device_map = { //this is used for identifying the device(s) to use when receiving pattern data, note it is different from Corsair because it supports less device types
    { 0, "all"},
    { 1, "keyboard"},
    { 2, "mouse"},
    { 6, "headset"}
};

int main(int argc, char** argv) {
    /*
    The main process for delivering RGB patterns to RAZER devices.
    Handles establishing a connection to the RAZER RESTful API and setting up a client socket connection to the main server process.
    */

    //as per the API's instructions, we must start be making a request to the URL with this format
    std::string json_payload = R"({
        "title": "Cross-API RGB Controller",
        "description": "This is a REST interface for the RGB Controller",
        "author": {
            "name": "RGBController",
            "contact": "www.razerzone.com"
        },
        "device_supported": ["keyboard", "mouse", "headset"],
        "category": "application"
    })";

    cpr::Response r = cpr::Post(RAZER_API_URL,
                    cpr::Body{json_payload},
                   cpr::Header{{"content-type", "application/json"}}
                );

    //using the response, it will contain a URI with the endpoint that we will interact with the send pattern data
    std::string uri;
    if (r.status_code == 200) {
        uri = r.text;
    } else {
        return 1;
    }
    auto json = nlohmann::json::parse(r.text);
    uri = json["uri"];

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

    while (true) { //now we continuously try to receive pattern data from the server process and display it
        try {

            bytesReceived = recv(recvSocket, recvBuf, sizeof(recvBuf) - 1, 0);   

            if (bytesReceived > 0) {
                recvBuf[bytesReceived] = '\0';  //null terminate the pattern data
                //std::cerr << "Received: " << recvBuf << "\n";
            } else if (bytesReceived == 0) {
                //std::cerr << "Connection closed by server.\n";
                nlohmann::json deletion_payload;
                auto res = cpr::Delete(
                    cpr::Url{uri},
                    cpr::Header{{"Content-Type", "application/json"}},
                    cpr::Body{deletion_payload.dump()}
                );
    
                closesocket(recvSocket);
                WSACleanup();
    
                return 0;

            } else {
                //terminate the connection gracefully with a DELETE request, then cleanup
                //std::cerr << "recv failed with error: " << WSAGetLastError() << "\n";
                nlohmann::json deletion_payload;
                auto res = cpr::Delete(
                    cpr::Url{uri},
                    cpr::Header{{"Content-Type", "application/json"}},
                    cpr::Body{deletion_payload.dump()}
                );
    
                closesocket(recvSocket);
                WSACleanup();
    
                return 0;
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

            //creating effect payload, our implementation uses a static effect that is constantly updated, note that the color is stored as BGR, bit shifted in reverse
            nlohmann::json effect_payload_json;
            effect_payload_json["effect"] = "CHROMA_STATIC";
            effect_payload_json["param"]["color"] = (b << 16) | (g << 8) | r;

            if (device_num > 0) {

                if (device_map.find(device_num) == device_map.end()) { //IMPORTANT: DO NOT TRY TO SEND REQUESTS WITH UNSUPPORTED DEVICE TYPES, though this will handle it
                    continue;
                }

                //use the device number to get the specific device we are working with
                std::string device = device_map[device_num];

                //send the effect to server to obtain effect id
                cpr::Response device_response = cpr::Post(cpr::Url{uri + "/" + device},
                                                    cpr::Header{{"content-type", "application/json"}},
                                                    cpr::Body{effect_payload_json.dump()}
                                                        );
                auto device_response_json = nlohmann::json::parse(device_response.text);
                std::string effect_id = device_response_json["id"];

                //now send the effect
                nlohmann::json id_payload;
                id_payload["id"] = effect_id;
                cpr::Put(cpr::Url{uri + "/effect"},
                            cpr::Header{{"Content-Type", "application/json"}},
                            cpr::Body{id_payload.dump()}
                            );

                //we can delete it right after as to not waste memory space
                cpr::Delete(cpr::Url{uri + "/effect"},
                        cpr::Header{{"Content-Type", "application/json"}},
                        cpr::Body{id_payload.dump()}
                        );

            } else { //this means we receiving device id 0, which means all devices

                //send effects to server to obtain effect ids
                std::vector<std::string> effect_ids;

                //TODO: we can do this with the device_map and a loop, but there's only 3 supported device types so far so this is ok for now

                cpr::Response keyboard_response = cpr::Post(cpr::Url{uri + "/" + "keyboard"},
                    cpr::Header{{"content-type", "application/json"}},
                    cpr::Body{effect_payload_json.dump()}
                        );
                auto keyboard_response_json = nlohmann::json::parse(keyboard_response.text);
                effect_ids.push_back(keyboard_response_json["id"]);

                cpr::Response mouse_response = cpr::Post(cpr::Url{uri + "/" + "mouse"},
                    cpr::Header{{"content-type", "application/json"}},
                    cpr::Body{effect_payload_json.dump()}
                        );
                auto mouse_response_json = nlohmann::json::parse(mouse_response.text);
                effect_ids.push_back(mouse_response_json["id"]);

                cpr::Response headset_response = cpr::Post(cpr::Url{uri + "/" + "headset"},
                    cpr::Header{{"content-type", "application/json"}},
                    cpr::Body{effect_payload_json.dump()}
                        );
                auto headset_response_json = nlohmann::json::parse(headset_response.text);
                effect_ids.push_back(headset_response_json["id"]);

                //now send all effects to the API
                nlohmann::json id_payload;
                id_payload["ids"] = effect_ids;
                cpr::Put(cpr::Url{uri + "/effect"},
                            cpr::Header{{"Content-Type", "application/json"}},
                            cpr::Body{id_payload.dump()}
                            );

                //we can delete it right after as to not waste memory space
                cpr::Delete(cpr::Url{uri + "/effect"},
                        cpr::Header{{"Content-Type", "application/json"}},
                        cpr::Body{id_payload.dump()}
                        );
            }
        
            //send a heartbeat to retain connection
            nlohmann::json heartbeat_payload;
            heartbeat_payload["tick"] = 1;
            cpr::PutAsync(cpr::Url{uri + "/heartbeat"},
                            cpr::Body{heartbeat_payload.dump()});

        } catch (...) { //we must terminate the connection to the API, done with a DELETE request
            nlohmann::json deletion_payload;
            auto res = cpr::Delete(
                cpr::Url{uri},
                cpr::Header{{"Content-Type", "application/json"}},
                cpr::Body{deletion_payload.dump()}
            );

            closesocket(recvSocket);
            WSACleanup();

            return 0;
        }
    }

    //terminate the connection to the API and cleanup
    nlohmann::json deletion_payload;
    auto res = cpr::Delete(
        cpr::Url{uri},
        cpr::Header{{"Content-Type", "application/json"}},
        cpr::Body{deletion_payload.dump()}
    );

    closesocket(recvSocket);
    WSACleanup();

    return 0;
}