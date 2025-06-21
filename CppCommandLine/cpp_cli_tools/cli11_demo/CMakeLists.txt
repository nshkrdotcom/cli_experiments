cmake_minimum_required(VERSION 3.16)
project(CLI11Demo VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# CLI11 is included as a header-only library

# Create the main executable
add_executable(cli_demo
    src/main.cpp
    src/config_manager.cpp
    src/command_executor.cpp
    src/llm_integration.cpp
)

# No linking needed for header-only CLI11

# Include directories
target_include_directories(cli_demo PRIVATE include)

# Compiler-specific options
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    target_compile_options(cli_demo PRIVATE -Wall -Wextra -O3)
endif()

# Installation
install(TARGETS cli_demo DESTINATION bin)