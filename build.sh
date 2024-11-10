#!/bin/bash

# Check if the --release flag is present
RELEASE_FLAG=false
if [[ "$1" == "--release" ]]; then
    RELEASE_FLAG=true
fi

# Step 0: Increment the version in the VERSION file
VERSION=$(cat VERSION)
IFS='.' read -r major minor patch <<< "$VERSION"
patch=$((patch + 1))
NEW_VERSION="$major.$minor.$patch"

# Update the VERSION file with the new version
echo "$NEW_VERSION" > VERSION
echo "Building version $NEW_VERSION"

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
cp -r SteamTinkerLaunch/ dist/FlashGameManager/SteamTinkerLaunch
mkdir -p dist/FlashGameManager/images
cp -r images/ dist/FlashGameManager

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
    ldd "$LIBQXCB_PATH" | grep "=>" | awk '{print $3}' | while read -r lib; do
        if [ -f "$lib" ]; then
            cp "$lib" dist/FlashGameManager/lib/
        fi
    done
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
cp run_manager.sh dist/FlashGameManager/run_manager.sh
chmod +x dist/FlashGameManager/run_manager.sh

# Step 8-9: If --release flag is provided: package the FlashGameManager folder into a versioned zip file, commit, tag, and create GitHub release
if [ "$RELEASE_FLAG" = true ]; then
    echo "Creating a new release: version $NEW_VERSION"

    cd dist
    zip -r "FlashGameManager_$NEW_VERSION.zip" FlashGameManager
    cd ..

    # Commit and tag the release
    git add VERSION dist/FlashGameManager_$NEW_VERSION.zip
    git commit -m "Release version $NEW_VERSION"
    git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"
    git push origin main
    git push origin "v$NEW_VERSION"

    # Create a GitHub release using GitHub CLI
    gh release create "v$NEW_VERSION" dist/FlashGameManager_$NEW_VERSION.zip --title "FlashGameManager v$NEW_VERSION" --notes "Release of version $NEW_VERSION"
else
    echo "Build complete. No release created as --release flag was not provided."
fi

# Notify user
echo "Installation complete. To run the application, use: ./run_manager.sh inside dist/FlashGameManager"
echo "The package has been zipped as FlashGameManager_$NEW_VERSION.zip in the dist folder."
