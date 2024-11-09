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

# Run the PyInstaller-built executable
./manager
