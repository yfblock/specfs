#!/bin/bash
# Regenerate virtio-blk driver from SYSSPEC specs, build, and optionally benchmark.
#
# Usage:
#   ./regen_virtio.sh              # generate + build
#   ./regen_virtio.sh benchmark    # generate + build + run benchmark
#   ./regen_virtio.sh clean        # clean generated files only

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_DIR="$SCRIPT_DIR/sysspec/virtio-blk-spec"
GEN_DIR="$SCRIPT_DIR/sysspec/vio-blk-gen"
KDIR="$SCRIPT_DIR/data/linux-6.14.4"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ─────────────────────────────── Clean ────────────────────────────────

clean_generated() {
    echo -e "${YELLOW}Cleaning generated files...${NC}"
    cd "$GEN_DIR"
    # Remove generated .c files (keep hand-written vblk_mod.c, hw_ops.h, Makefile)
    find . -name "*.c" ! -name "vblk_mod.c" -delete 2>/dev/null || true
    find . -name "*.h" ! -name "hw_ops.h" -delete 2>/dev/null || true
    rm -f vblk.ko vblk.mod vblk.mod.c vblk.mod.o vblk.o .vblk.*.cmd Module.symvers modules.order
    find . -name "*.o" -delete 2>/dev/null || true
    find . -name ".*.cmd" -delete 2>/dev/null || true
    find . -name "*.o.d" -delete 2>/dev/null || true
    find . -name ".tmp_*" -delete 2>/dev/null || true
    echo -e "${GREEN}Generated files cleaned.${NC}"
}

# ─────────────────────────────── Generate ──────────────────────────────

generate() {
    echo -e "${BLUE}[1/3] Generating code from specs...${NC}"
    cd "$SCRIPT_DIR"
    uv run python gen_virtio.py generate
    echo -e "${GREEN}Code generation complete.${NC}"
}

# ─────────────────────────────── Evolve ────────────────────────────────

evolve() {
    echo -e "${BLUE}[1/3] Evolving code with optimized specs...${NC}"
    cd "$SCRIPT_DIR"
    uv run python gen_virtio.py evolve
    echo -e "${GREEN}Evolution complete.${NC}"
}

# ─────────────────────────────── Build ─────────────────────────────────

build() {
    echo -e "${BLUE}[2/3] Building kernel module...${NC}"
    if [ ! -d "$KDIR" ]; then
        echo -e "${RED}ERROR: Kernel source not found at $KDIR${NC}"
        echo -e "${RED}Expected: $KDIR (linux-6.14.4 kernel tree)${NC}"
        exit 1
    fi
    cd "$GEN_DIR"
    KDIR="$KDIR" make 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Build successful: $GEN_DIR/vblk.ko${NC}"
    else
        echo -e "${RED}Build failed! Run '$0 clean' and try again.${NC}"
        exit 1
    fi
}

# ─────────────────────────────── Benchmark ─────────────────────────────

benchmark() {
    echo -e "${BLUE}[3/3] Running benchmark...${NC}"
    rm -f "$SCRIPT_DIR/data/initramfs_bench.cpio"
    "$SCRIPT_DIR/run_benchmark.sh"
}

# ─────────────────────────────── Main ──────────────────────────────────

ACTION="${1:-build}"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  SYSSPEC Virtio-Blk Regeneration${NC}"
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
    evolve-benchmark)
        evolve
        build
        benchmark
        ;;
    build)
        generate
        build
        ;;
    benchmark)
        generate
        build
        benchmark
        ;;
    *)
        echo "Usage: $0 {generate|evolve|evolve-benchmark|build|benchmark|clean}"
        echo ""
        echo "  generate          Generate code from specs only"
        echo "  evolve            Evolve code with optimized specs + build"
        echo "  evolve-benchmark  Evolve + build + run benchmark"
        echo "  build             Generate + compile kernel module (default)"
        echo "  benchmark         Generate + compile + run fio benchmark"
        echo "  clean             Remove all generated files"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
