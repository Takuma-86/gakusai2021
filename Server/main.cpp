#include <sys/socket.h> //socket(), bind(), sendto(), recvfrom()
#include <arpa/inet.h> // struct sockaddr_in, struct sockaddr, inet_ntoa(), inet_aton()
#include <unistd.h> //close()
#include <mqueue.h>
#include <cstdint>
#include <iostream>
#include <mutex>
#include <thread>
#include <opencv2/opencv.hpp>
#include <atomic>

#include "udpTx.h"
#include "errorhandling.h"
#include "json/json11.hpp"

using namespace json11;

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

std::string globalEncodedImageContent;
std::atomic<bool> stop_tx_thread_flag(false);
std::atomic<bool> stop_rx_thread_flag(false);

void RxCommunicatorThread(std::string defualtMovementCode) {    // Thread for Receiving data from client. TCP connection.
    int i;
    char *buff;
    mqd_t mqd;
    const int flags = O_WRONLY | O_CREAT;
    mode_t mode = 0777;
    const char *mq_name = "/gakusai2021.1"; // Name of message queue.
    char *sendedMovementCode = const_cast<char *>(defualtMovementCode.c_str());
    bool tcp_succeed_flag(false);
    mqd = mq_open(mq_name, flags, mode);
    if (mqd == -1) {
        error_exit("Message queue open failed at RxCommunicatorThread, Exiting.");
    }
    while (!stop_rx_thread_flag) {
        // Getting movement data from client via tcp.
        // Sending the data to python process with message queue.
        buff = (char *) calloc(strlen(sendedMovementCode) + 1, sizeof(char));
        strcpy(buff, sendedMovementCode);
        if (!tcp_succeed_flag) {
            if (mq_send(mqd, buff, strlen(buff), 0) == -1) {
                error_exit("Message Queue send faild at RxCommunicatorThread, Exiting.");
            }

        }
    }
    if (mq_close(mqd) == -1)
        error_exit("Message queue close failed at RxCommunicatorThread, Exiting anyway.");
}

void TxCommunicatorThread() {    // Thread for Transferring data. Mainly transferring webcam image. UDP connection.
    std::string encodedImageContent;
    udpTx udp("192.168.0.1", 50041);
    while (!stop_tx_thread_flag) {
        pthread_mutex_lock(&mutex);
        // Getting encoded image content from main process, critical behavior.
        encodedImageContent = globalEncodedImageContent;
        // Ending critical process.
        pthread_mutex_unlock(&mutex);
        if (!(encodedImageContent.empty())) {  // Check if there is a worthwhile content.
            udp.send(encodedImageContent);  // Send encoded image via udp.
        }
    }
}

int main(int argc, char *argv[]) {
    // Some initial stuff for opencv.
    cv::VideoCapture cap;
    cv::Mat frame;
    std::vector<uchar> buff;

    std::string stringDefualtMovementCode(R"({"joystick": {"r": 0.8, "sita": 1}, "shoot": 0, "LR": 0})");

    //Initializing threads;
    std::thread Rx(RxCommunicatorThread, stringDefualtMovementCode);
    std::thread Tx(TxCommunicatorThread);
    // Setting up camera streaming via opencv.
    cap.open(0);
    if (!cap.isOpened()) {
        printf("Could not open stream");
        return -1;
    }
    double vidWidth = cap.get(cv::CAP_PROP_FRAME_WIDTH);
    double vidHeight = cap.get(cv::CAP_PROP_FRAME_HEIGHT);
    std::cout << "Video Width is " << vidWidth << std::endl;
    std::cout << "Video Height is " << vidHeight << std::endl;
    cap >> frame;
    while (!frame.empty()) {
        // Encoding camera stream with webp.
        cv::imencode(".jpg", frame, buff, std::vector<int>()); // Didn't need libwebp?
        std::string encoded_content(buff.begin(), buff.end());
        pthread_mutex_lock(&mutex);
        // Passing encoded image content to thread, critical behavior.
        globalEncodedImageContent = encoded_content;
        // Finished passing data. Finished critical behavior.
        pthread_mutex_unlock(&mutex);
        cap >> frame;
    }
    cap.release();
}