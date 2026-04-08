# Use
# cmake prep: cmake -S . -B build
# compilation: cmake --build build

cmake_minimum_required(VERSION 3.25)

project(Fitter
  VERSION 0.0.1
  LANGUAGES CXX
)

find_package(ROOT REQUIRED COMPONENTS RooFit ROOTDataFrame)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
find_package(yaml-cpp REQUIRED)

add_subdirectory(src)

# file(GLOB CFG_FILES "cfg/*.yml")
# file(COPY ${CFG_FILES} DESTINATION ${CMAKE_BINARY_DIR}/bin)

# target_link_libraries(helloWorld yaml-cpp)