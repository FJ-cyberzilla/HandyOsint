#!/bin/bash

# HandyOsint Production Launcher

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║               H A N D Y O S I N T   v2.4                  ║"
echo "║               16-Bit Vintage Command Center               ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;92m'
CYAN='\033[0;96m'
RED='\033[0;91m'
RESET='\033[0m'

# Function to check dependencies
check_deps() {
    echo -e "${CYAN}[*] Checking dependencies...${RESET}"
    
    deps=("python3" "pip3")
    missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v $dep &> /dev/null; then
            missing+=($dep)
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        echo -e "${RED}[✗] Missing dependencies: ${missing[@]}${RESET}"
        return 1
    fi
    
    echo -e "${GREEN}[✓] Dependencies found${RESET}"
    return 0
}

# Function to setup environment
setup_env() {
    echo -e "${CYAN}[*] Setting up environment...${RESET}"
    
    # Create necessary directories
    mkdir -p data logs reports
    
    # Check if requirements are installed
    if ! python3 -c "import aiohttp, aioconsole, aiofiles" &> /dev/null; then
        echo -e "${CYAN}[*] Installing requirements...${RESET}"
        pip3 install -r requirements.txt
    fi
    
    echo -e "${GREEN}[✓] Environment ready${RESET}"
}

# Function to run system check
run_checks() {
    echo -e "${CYAN}[*] Running system checks...${RESET}"
    
    if [ -f "system_check.py" ]; then
        python3 system_check.py
        return $?
    else
        echo -e "${RED}[✗] system_check.py not found${RESET}"
        return 1
    fi
}

# Function to launch application
launch_app() {
    echo -e "${CYAN}[*] Launching HandyOsint...${RESET}"
    echo ""
    
    python3 main.py
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}[✓] Application exited normally${RESET}"
    elif [ $EXIT_CODE -eq 130 ]; then
        echo -e "${CYAN}[!] Application interrupted by user${RESET}"
    else
        echo -e "${RED}[✗] Application exited with code $EXIT_CODE${RESET}"
    fi
    
    return $EXIT_CODE
}

# Main execution
main() {
    echo -e "${CYAN}HandyOsint Production Launcher${RESET}"
    echo -e "${CYAN}===============================${RESET}"
    echo ""
    
    # Check dependencies
    if ! check_deps; then
        exit 1
    fi
    
    # Setup environment
    setup_env
    
    # Run checks
    if ! run_checks; then
        echo -e "${RED}[✗] System checks failed${RESET}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Launch application
    launch_app
    
    echo ""
    echo -e "${CYAN}Session ended at: $(date)${RESET}"
}

# Run main function
main "$@"
