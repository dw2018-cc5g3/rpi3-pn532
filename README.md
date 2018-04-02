# rpi3-pn532
interface code between the RPi 3 and PN532 breakout board (for NFC)

## Setup

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

    $ mkdir build
    $ cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=~/.local ..
    $ make install

Congratulations, you just installed nfc-bindings. Now test that it works on Python 3 by doing:

    $ cd ..    # since you are still in the build directory
    $ python3 python/examples/quick_start_example.py
 
 
Then execute the script in the main directory of this repo.
