cmake_minimum_required(VERSION 3.16)
project(gecko_browser LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(gecko_browser
    src/main.cpp
    src/browser_app.cpp
    src/gecko_bridge.cpp
)

target_include_directories(gecko_browser PRIVATE include)

target_compile_options(gecko_browser PRIVATE
    -Wall
    -Wextra
    -Wpedantic
)
