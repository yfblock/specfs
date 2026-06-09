#!/bin/bash
# Regenerate uart16550 driver from SYSSPEC specs, build, and optionally test.
#
# Usage:
#   ./regen_uart16550.sh              # generate + build
#   ./regen_uart16550.sh test         # generate + build + QEMU test
#   ./regen_uart16550.sh clean        # clean generated files only
#
# First-time QEMU environment:
#   ./scripts/setup-qemu-env.sh --kernels

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN_DIR="$SCRIPT_DIR/sysspec/uart16550-gen"
KDIR="$SCRIPT_DIR/data/linux-6.14.4"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clean_generated() {
    echo -e "${YELLOW}Cleaning generated files...${NC}"
    cd "$GEN_DIR"
    rm -rf uart
    rm -f common.h
    rm -f uart16550.ko uart16550.mod uart16550.mod.c uart16550.mod.o uart16550.o .uart16550.*.cmd Module.symvers modules.order
    find . -name "*.o" -delete 2>/dev/null || true
    find . -name ".*.cmd" -delete 2>/dev/null || true
    find . -name "*.o.d" -delete 2>/dev/null || true
    find . -name ".tmp_*" -delete 2>/dev/null || true
    echo -e "${GREEN}Generated files cleaned.${NC}"
}

generate() {
    echo -e "${BLUE}[1/2] Generating code from specs...${NC}"
    cd "$SCRIPT_DIR"
    uv run python gen_uart16550.py generate
    echo -e "${GREEN}Code generation complete.${NC}"
}

evolve() {
    echo -e "${BLUE}[1/2] Evolving code with optimized specs...${NC}"
    cd "$SCRIPT_DIR"
    uv run python gen_uart16550.py evolve
    echo -e "${GREEN}Evolution complete.${NC}"
}

build() {
    echo -e "${BLUE}[2/2] Building kernel module...${NC}"
    if [ ! -d "$KDIR" ]; then
        echo -e "${RED}ERROR: Kernel source not found at $KDIR${NC}"
        echo -e "${RED}Run: ./scripts/setup-qemu-env.sh${NC}"
        exit 1
    fi
    cd "$GEN_DIR"
    KDIR="$KDIR" make 2>&1
    echo -e "${GREEN}Build successful: $GEN_DIR/uart16550.ko${NC}"
}

test_qemu() {
    echo -e "${BLUE}[3/3] Running QEMU UART test...${NC}"
    "$SCRIPT_DIR/test_uart_qemu.sh"
}

ACTION="${1:-build}"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  SYSSPEC UART16550 Regeneration${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

case "$ACTION" in
    clean)
        clean_generated
        ;;
    generate)
        generate
        ;;
    evolve)
        evolve
        build
        ;;
    build)
        generate
        build
        ;;
    test)
        generate
        build
        test_qemu
        ;;
    *)
        echo "Usage: $0 {generate|evolve|build|test|clean}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
