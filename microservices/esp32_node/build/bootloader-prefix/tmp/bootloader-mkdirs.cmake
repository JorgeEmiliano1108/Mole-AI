# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/deepmole/esp/esp-idf/components/bootloader/subproject"
  "/home/deepmole/Escritorio/Mole-AI/microservices/esp32_node/build/bootloader"
  "/home/deepmole/Escritorio/Mole-AI/microservices/esp32_node/build/bootloader-prefix"
  "/home/deepmole/Escritorio/Mole-AI/microservices/esp32_node/build/bootloader-prefix/tmp"
  "/home/deepmole/Escritorio/Mole-AI/microservices/esp32_node/build/bootloader-prefix/src/bootloader-stamp"
  "/home/deepmole/Escritorio/Mole-AI/microservices/esp32_node/build/bootloader-prefix/src"
  "/home/deepmole/Escritorio/Mole-AI/microservices/esp32_node/build/bootloader-prefix/src/bootloader-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/deepmole/Escritorio/Mole-AI/microservices/esp32_node/build/bootloader-prefix/src/bootloader-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/deepmole/Escritorio/Mole-AI/microservices/esp32_node/build/bootloader-prefix/src/bootloader-stamp${cfgdir}") # cfgdir has leading slash
endif()
