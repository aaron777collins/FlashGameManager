#!/bin/bash

# Set the path to the Qt platform plugins
export QT_QPA_PLATFORM_PLUGIN_PATH=$PWD/platforms

# Preload OpenSSL 1.1 library to ensure compatibility
export LD_PRELOAD=$PWD/lib/libssl.so.1.1:$PWD/lib/libcrypto.so.1.1

# Add the custom lib folder and OpenSSL 1.1 path to the library path
export LD_LIBRARY_PATH=$PWD/lib:$LD_LIBRARY_PATH

# Additional environment variables for XCB
export QT_XCB_GL_INTEGRATION=none
export QT_DEBUG_PLUGINS=1  # Enables debug output for Qt plugin loading

# Define the target data directory path
TARGET_DATA_DIR="$HOME/.local/share/FlashGameManager/data/FlashGameManager/game_data/Flashpoint"

# Check if the Flashpoint folder already exists at the target location
if [ ! -d "$TARGET_DATA_DIR" ]; then
    # Ensure the target directory exists
    mkdir -p "$TARGET_DATA_DIR"

    # Copy the Flashpoint folder and its contents to the target data directory
    cp -r Flashpoint/* "$TARGET_DATA_DIR"
    echo "Flashpoint folder copied to $TARGET_DATA_DIR"
else
    echo "Flashpoint folder already exists at $TARGET_DATA_DIR; skipping copy."
fi

# Run the PyInstaller-built executable
./manager
