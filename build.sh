#!/bin/bash

# Step 1: Set up the virtual environment
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt

# Step 2: Build the executable with PyInstaller
pyinstaller manager.py --onefile --windowed --hidden-import=pkgutil --hidden-import=PyQt5.sip --hidden-import=PyQt5.QtCore

# Step 3: Create the distribution folder
mkdir -p dist/FlashGameManager
cp dist/manager dist/FlashGameManager/manager
cp -r Flashpoint/ dist/FlashGameManager/Flashpoint

# Step 4: Locate and copy the required Qt platform plugins
QT_PLUGINS_DIR=$(find $(python -c "import PyQt5; print(PyQt5.__path__[0])") -type d -name "platforms" | head -n 1)

if [ -d "$QT_PLUGINS_DIR" ]; then
    mkdir -p dist/FlashGameManager/platforms
    cp "$QT_PLUGINS_DIR"/* dist/FlashGameManager/platforms/
else
    echo "Warning: Could not locate the Qt platforms directory. Please ensure the 'xcb' plugin is available."
fi

# Step 5: Locate libqxcb.so and copy all dependencies to lib directory
mkdir -p dist/FlashGameManager/lib
LIBQXCB_PATH="$QT_PLUGINS_DIR/libqxcb.so"

if [ -f "$LIBQXCB_PATH" ]; then
    # Copy libqxcb.so dependencies to the lib folder
    ldd "$LIBQXCB_PATH" | grep "=>" | awk '{print $3}' | while read -r lib; do
        if [ -f "$lib" ]; then
            cp "$lib" dist/FlashGameManager/lib/
        fi
    done
    # Copy libqxcb.so itself
    cp "$LIBQXCB_PATH" dist/FlashGameManager/platforms/
else
    echo "Error: libqxcb.so not found."
fi

# Step 6: Ensure OpenSSL 1.1 libraries are included if needed
if [ -f /usr/lib/libssl.so.1.1 ] && [ -f /usr/lib/libcrypto.so.1.1 ]; then
    cp /usr/lib/libssl.so.1.1 dist/FlashGameManager/lib/
    cp /usr/lib/libcrypto.so.1.1 dist/FlashGameManager/lib/
else
    echo "Warning: OpenSSL 1.1 libraries not found on the system."
fi

# Step 7: Create a startup script to set environment variables for Qt plugins and libraries
echo '#!/bin/bash' > dist/FlashGameManager/run_manager.sh
echo 'export QT_QPA_PLATFORM_PLUGIN_PATH=$PWD/platforms' >> dist/FlashGameManager/run_manager.sh
echo 'export LD_LIBRARY_PATH=$PWD/lib:$LD_LIBRARY_PATH' >> dist/FlashGameManager/run_manager.sh
echo './manager' >> dist/FlashGameManager/run_manager.sh
chmod +x dist/FlashGameManager/run_manager.sh

# Notify user
echo "Installation complete. To run the application, use: ./run_manager.sh inside dist/FlashGameManager"
