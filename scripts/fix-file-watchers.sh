#!/bin/bash
# Fix for ENOSPC: System limit for number of file watchers reached

echo "=== File Watcher Limit Fix ==="
echo ""

# Check current limit
CURRENT_LIMIT=$(cat /proc/sys/fs/inotify/max_user_watches)
echo "Current limit: $CURRENT_LIMIT"
echo "Recommended limit: 524288"
echo ""

# Temporary fix (lasts until reboot)
echo "Step 1: Apply temporary fix (requires sudo)..."
echo "Running: sudo sysctl fs.inotify.max_user_watches=524288"
sudo sysctl fs.inotify.max_user_watches=524288

if [ $? -eq 0 ]; then
    echo "✓ Temporary fix applied successfully"
    echo ""

    # Permanent fix
    echo "Step 2: Make change permanent..."

    # Check if the setting already exists
    if grep -q "fs.inotify.max_user_watches" /etc/sysctl.conf; then
        echo "Setting already exists in /etc/sysctl.conf"
        sudo sed -i 's/fs.inotify.max_user_watches=.*/fs.inotify.max_user_watches=524288/' /etc/sysctl.conf
    else
        echo "Adding setting to /etc/sysctl.conf"
        echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf > /dev/null
    fi

    if [ $? -eq 0 ]; then
        echo "✓ Permanent fix applied successfully"
        echo ""

        # Verify
        NEW_LIMIT=$(cat /proc/sys/fs/inotify/max_user_watches)
        echo "Step 3: Verification"
        echo "New limit: $NEW_LIMIT"
        echo ""

        if [ "$NEW_LIMIT" -eq 524288 ]; then
            echo "✓ Fix successful! The file watcher limit has been increased."
            echo ""
            echo "You can now restart Claude Code or any other affected applications."
        else
            echo "⚠ Warning: The limit was not set correctly. Please check for errors above."
        fi
    else
        echo "✗ Failed to make permanent change. Please check permissions."
    fi
else
    echo "✗ Failed to apply temporary fix. Please check sudo permissions."
    exit 1
fi
