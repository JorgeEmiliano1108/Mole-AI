source $HOME/esp/esp-idf/export.sh 

cd ~/Escritorio/Mole-AI/microservices/esp32_node

idf.py fullclean  

idf.py build

idf.py -p /dev/ttyUSB0 -b 115200 flash monitor

idf.py -p /dev/ttyUSB0 -b 115200 erase-flash flash monitor

idf.py menuconfig

sudo chmod a+rw /dev/ttyUSB0 #darle permisos al puerto usb
