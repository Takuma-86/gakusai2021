cmake_minimum_required(VERSION 3.16)
project(Server)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pthread -lrt")

find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

add_executable(Server main.cpp udpTx.h errorhandling.h json/json11.hpp json/json11.cpp)
target_link_libraries(Server ${OpenCV_LIBS})