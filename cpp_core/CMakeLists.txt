cmake_minimum_required(VERSION 3.20)
project(cpp_core)

set(CMAKE_CXX_STANDARD 17)

add_library(backend_logic SHARED src/library.cpp)

target_link_options(backend_logic PRIVATE -static)