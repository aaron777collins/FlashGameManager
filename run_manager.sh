#!/bin/bash

# Set the path to the Qt platform plugins
export QT_QPA_PLATFORM_PLUGIN_PATH=$PWD/platforms

# Add the custom lib folder and OpenSSL 1.1 path to the library path
export LD_LIBRARY_PATH=$PWD/lib:$LD_LIBRARY_PATH

# Define the target data directory path
FLASHPOINT_TARGET_DATA_DIR="$HOME/.local/share/FlashGameManager/data/FlashGameManager/game_data/flashpoint-nano"

echo "Initializing.."

# Check if the Flashpoint folder already exists at the target location
if [ ! -d "$FLASHPOINT_TARGET_DATA_DIR" ]; then
    # Ensure the target directory exists
    mkdir -p "$FLASHPOINT_TARGET_DATA_DIR"

    # Copy the Flashpoint folder and its contents to the target data directory
    cp -r flashpoint-nano/* "$FLASHPOINT_TARGET_DATA_DIR"
    echo "Flashpoint folder copied to $FLASHPOINT_TARGET_DATA_DIR"
else
    echo "Flashpoint folder already exists at $FLASHPOINT_TARGET_DATA_DIR; skipping copy."
fi

# Define the target data directory path
STEAMTINKERLAUNCH_TARGET_DATA_DIR="$HOME/.local/share/FlashGameManager/data/FlashGameManager/game_data/SteamTinkerLaunch"

# Check if the SteamTinkerLaunch folder already exists at the target location
if [ ! -d "$STEAMTINKERLAUNCH_TARGET_DATA_DIR" ]; then
    # Ensure the target directory exists
    mkdir -p "$STEAMTINKERLAUNCH_TARGET_DATA_DIR"

    # Copy the SteamTinkerLaunch folder and its contents to the target data directory
    cp -r SteamTinkerLaunch/* "$STEAMTINKERLAUNCH_TARGET_DATA_DIR"
    echo "SteamTinkerLaunch folder copied to $STEAMTINKERLAUNCH_TARGET_DATA_DIR"
else
    echo "SteamTinkerLaunch folder already exists at $STEAMTINKERLAUNCH_TARGET_DATA_DIR; skipping copy."
fi

# Define the target data directory path
IMAGES_TARGET_DATA_DIR="$HOME/.local/share/FlashGameManager/data/FlashGameManager/game_data/images"

# Check if the SteamTinkerLaunch folder already exists at the target location
if [ ! -d "$IMAGES_TARGET_DATA_DIR" ]; then
    # Ensure the target directory exists
    mkdir -p "$IMAGES_TARGET_DATA_DIR"

    # Copy the SteamTinkerLaunch folder and its contents to the target data directory
    cp -r images/* "$IMAGES_TARGET_DATA_DIR"
    echo "images folder copied to $IMAGES_TARGET_DATA_DIR"
else
    echo "images folder already exists at $IMAGES_TARGET_DATA_DIR; skipping copy."
fi

# Run the PyInstaller-built executable
./manager
