#!/bin/bash

# Ensure Flatpak is installed
if ! command -v flatpak &> /dev/null; then
    echo "Flatpak is not installed. Please install it first."
    exit 1
fi

# Check if the Ruffle Flatpak is installed
if ! flatpak list | grep -q "rs.ruffle.Ruffle"; then
    echo "Installing Ruffle Flatpak..."
    flatpak install --user -y flathub rs.ruffle.Ruffle
fi

# Launch Ruffle using Flatpak
echo "Launching Ruffle with $entry_launch_command"
flatpak run --user  --env=http_proxy=http://127.0.0.1:22500 --env=https_proxy=http://127.0.0.1:22500 rs.ruffle.Ruffle --proxy http://127.0.0.1:22500 --no-gui "$entry_launch_command"
