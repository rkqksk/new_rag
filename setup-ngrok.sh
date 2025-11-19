#!/bin/bash

echo "=========================================="
echo "ngrok Setup Script"
echo "=========================================="
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed!"
    echo "Install with: sudo snap install ngrok"
    exit 1
fi

echo "✅ ngrok is installed ($(ngrok version))"
echo ""

# Prompt for authtoken
echo "📝 Please enter your ngrok authtoken"
echo "   (Get it from: https://dashboard.ngrok.com/get-started/your-authtoken)"
echo ""
read -p "Authtoken: " AUTHTOKEN

if [ -z "$AUTHTOKEN" ]; then
    echo "❌ No authtoken provided!"
    exit 1
fi

# Configure ngrok
echo ""
echo "🔧 Configuring ngrok..."
ngrok config add-authtoken "$AUTHTOKEN"

if [ $? -eq 0 ]; then
    echo "✅ ngrok configured successfully!"
    echo ""
    echo "📍 Configuration saved to: ~/.config/ngrok/ngrok.yml"
    echo ""
    echo "🚀 Test your tunnel with:"
    echo "   ngrok http 8001"
    echo ""
else
    echo "❌ Failed to configure ngrok!"
    exit 1
fi

