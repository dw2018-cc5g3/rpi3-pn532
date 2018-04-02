# rpi3-pn532
interface code between the RPi 3 and PN532 breakout board (for NFC)

## Setup

### Installing libnfc, nfc-bindings and friends

You need to install libnfc onto the RPi for this to work. Do:

    $ sudo apt install libusb-dev libnfc-dev

Then you need to install Python 3 to libnfc bindings. This has a few prerequisites...:

    $ sudo apt install cmake swig3.0
    $ git clone https://github.com/xantares/nfc-bindings.git
    $ cd nfc-bindings

You just downloaded the nfc-bindings source, but this library targets Python 2 by default. Using a text editor like `nano`, change the settings to target Python 3:

    $ nano python/CMakeLists.txt

Change the lines that look like this:

    find_package (PythonInterp)
    find_package (PythonLibs)

To this:

    find_package (PythonInterp 3 REQUIRED)
    find_package (PythonLibs 3 REQUIRED)

Save and exit. This tells CMake, the compilation system, to target Python 3 instead of 2.

Now you need to do some final tweaking before installing nfc-bindings onto your Pi:

    $ mkdir build        # this prevents CMake from polluting the repo with build output 
    $ cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=~/.local ..
    $ make install

Congratulations, you just installed nfc-bindings. 

### Raspberry Pi GPIO setup

On the PN532 board, make sure UART mode is selected. Check jumpers `SEL0` and `SEL1`, and make sure they are both at the `OFF` position. Wire up the board to the Pi GPIO pins like so:

- PI `GND` <---> `GND` PN532
- PI `3V3` <---> `3.3V` PN532
  - **DO NOT MIX THESE TWO PINS UP!** Any pins labelled `GND` and `3V3` on the PI will do, but make sure you connect `GND` to `GND` and `3.3V` to `3.3V`.

- PI `TXD0` (pin 8) <---> `RX` PN532
- PI `RXD0` (pin 10) <---> `TX` PN532

By default, these two pins are not accessible by software running on the Pi since the Linux kernel uses these two pins as a serial connection to expose a TTY. If you didn't understand that, that's okay, just follow this. Open up a terminal and type `sudo raspi-config`, then select option 5 `Interfacing options`, then option P6 `Serial`. Answer `No` to the first question and `Yes` to the second. This will disable the kernel serial console while leaving the serial (UART) hardware enabled.

### libnfc setup, telling it where to find the PN532 reader

Libnfc won't be able to find the PN532 by default since it won't think to look for it on the serial connection. So you need to explicitly tell it to do this with a "connstring". The connstring for the Pi/PN532/UART combo is:

    pn532_uart:/dev/ttyS0

You need to pass this string into the nfc initialization like so:

    nfc.open(context, 'pn532_uart:/dev/ttyS0')

### Bringing everything together

There is a little script in the nfc-bindings source that will test the reader for you. First:

    $ cd ..        # since you are still in the build directory

Then change to the example directory:

    $ cd python/examples
 
Modify the test script `quick_start_example.py` to use this connstring:

    $ nano quick_start_example.py

Change the `pnd = nfc.open(context)` line accordingly. Then test with Python 3:

    $ python3 quick_start_example.py

Tap a MIFARE tag or card onto the reader. Your hostel room keycard will work.

## Actual Python interface 

### Script mode

Simple test:

    $ python3 reader.py

Then tap a CEPAS card (your SUTD red card works, so does any ezlink card). If all went well you should see something like this:

    Tap a CEPAS card...
    Your CAN: 1234 5678 9012 3456

### Import mode

This snippet of code will wait until a suitable card is tapped, then save the CAN as a single 16-character string (like `1234567890123456`):

    import reader
    can = reader.block_for_can(spaces=False)

Use the CAN as a user ID or something.