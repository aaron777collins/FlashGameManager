#!/bin/bash

# Add the Flathub repository (if not already added)
flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install the KDE Platform and SDK runtimes
flatpak --user install -y flathub org.kde.Platform//5.15
flatpak --user install -y flathub org.kde.Sdk//5.15

# Build and install the Flatpak
flatpak-builder --user --install --force-clean build-dir flash_game_manager.yaml
