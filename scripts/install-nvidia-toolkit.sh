#!/bin/bash
# Install NVIDIA Container Toolkit

set -e

echo "Installing NVIDIA Container Toolkit..."

# 1. Download and install GPG key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# 2. Add repository
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 3. Update package list
sudo apt-get update

# 4. Install nvidia-container-toolkit
sudo apt-get install -y nvidia-container-toolkit

# 5. Restart Docker
sudo systemctl restart docker

echo "✓ Installation complete!"
