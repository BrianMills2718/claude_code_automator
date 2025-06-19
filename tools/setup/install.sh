#!/bin/bash
# CC_AUTOMATOR3 Installation Script

echo "Installing CC_AUTOMATOR3..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create convenience scripts
mkdir -p ~/bin

# Create cc-setup command
cat > ~/bin/cc-setup << EOF
#!/bin/bash
python $SCRIPT_DIR/setup.py "\$@"
EOF

# Create cc-run command
cat > ~/bin/cc-run << EOF
#!/bin/bash
python $SCRIPT_DIR/run.py "\$@"
EOF

# Make scripts executable
chmod +x ~/bin/cc-setup
chmod +x ~/bin/cc-run

# Add ~/bin to PATH if not already there
if ! echo $PATH | grep -q "$HOME/bin"; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    echo "Added ~/bin to PATH in ~/.bashrc"
fi

echo "Installation complete!"
echo ""
echo "Available commands:"
echo "  cc-setup  - Set up a new project"
echo "  cc-run    - Run the automator in current directory"
echo ""
echo "Usage:"
echo "  cd /path/to/new/project"
echo "  cc-setup --project ."
echo "  cc-run"
echo ""
echo "Note: You may need to run 'source ~/.bashrc' or open a new terminal"