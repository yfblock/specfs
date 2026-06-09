#!/bin/bash
# Prepare QEMU test/benchmark environment for SYSSPEC virtio-blk work.
#
# Downloads and extracts the Linux kernel tree (if needed), checks host
# dependencies, and optionally builds kernel images and a static fio binary.
# Disk images (.img) and initramfs (.cpio) are created on demand by
# test_qemu.sh and run_benchmark.sh — they are not stored here.
#
# Usage:
#   ./scripts/setup-qemu-env.sh              # deps + kernel tree (fast)
#   ./scripts/setup-qemu-env.sh --kernels    # also build bzImage variants
#   ./scripts/setup-qemu-env.sh --fio        # also build static fio
#   ./scripts/setup-qemu-env.sh --all        # kernels + fio
#   ./scripts/setup-qemu-env.sh --force      # rebuild even if outputs exist

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"

KERNEL_VERSION="6.14.4"
KERNEL_TARBALL="linux-${KERNEL_VERSION}.tar.xz"
KERNEL_URL="https://cdn.kernel.org/pub/linux/kernel/v6.x/${KERNEL_TARBALL}"
KERNEL_DIR="$DATA_DIR/linux-${KERNEL_VERSION}"

KERNEL_NOVBLK="$DATA_DIR/bzImage-${KERNEL_VERSION}-novblk"
KERNEL_BUILTIN="$DATA_DIR/bzImage-${KERNEL_VERSION}-builtin"
KERNEL_DEFAULT="$DATA_DIR/bzImage"
FIO_BIN="$DATA_DIR/fio"

BUILD_KERNELS=0
BUILD_FIO=0
FORCE=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --kernels   Build bzImage-${KERNEL_VERSION}-novblk and -builtin
  --fio       Build static fio binary at data/fio
  --all       Equivalent to --kernels --fio
  --force     Rebuild kernel images / fio even if they already exist
  -h, --help  Show this help

Examples:
  $0                    # Check tools and ensure kernel source tree
  $0 --all              # Full one-time setup (kernel compile may take a while)
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --kernels) BUILD_KERNELS=1 ;;
        --fio)     BUILD_FIO=1 ;;
        --all)     BUILD_KERNELS=1; BUILD_FIO=1 ;;
        --force)   FORCE=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; usage; exit 1 ;;
    esac
    shift
done

need_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${RED}Missing command: $1${NC}"
        return 1
    fi
}

check_deps() {
    echo -e "${BLUE}[1/4] Checking host dependencies...${NC}"
    local missing=0

    for cmd in qemu-system-x86_64 gcc make git cpio gzip bc flex bison; do
        need_cmd "$cmd" || missing=1
    done

    if ! command -v busybox &>/dev/null && [ ! -x /usr/bin/busybox ]; then
        echo -e "${RED}Missing: busybox (sudo apt install busybox)${NC}"
        missing=1
    fi

    if [ ! -c /dev/kvm ]; then
        echo -e "${YELLOW}  Note: /dev/kvm not found — QEMU will use slower TCG emulation.${NC}"
    else
        echo -e "${GREEN}  KVM available.${NC}"
    fi

    if [ "$missing" -ne 0 ]; then
        echo ""
        echo -e "${YELLOW}Suggested packages (Debian/Ubuntu):${NC}"
        echo "  sudo apt-get install -y qemu-system-x86 busybox build-essential \\"
        echo "    bc cpio gzip flex bison libssl-dev libelf-dev git"
        exit 1
    fi

    echo -e "${GREEN}  Host dependencies OK.${NC}"
}

fetch_kernel_tree() {
    echo -e "${BLUE}[2/4] Ensuring kernel source tree (${KERNEL_VERSION})...${NC}"

    if [ -d "$KERNEL_DIR" ] && [ -f "$KERNEL_DIR/Makefile" ]; then
        echo -e "${GREEN}  Kernel tree already present: $KERNEL_DIR${NC}"
        return
    fi

    mkdir -p "$DATA_DIR"

    if [ ! -f "$DATA_DIR/$KERNEL_TARBALL" ]; then
        echo -e "${YELLOW}  Downloading ${KERNEL_TARBALL}...${NC}"
        if command -v wget &>/dev/null; then
            wget -O "$DATA_DIR/$KERNEL_TARBALL" "$KERNEL_URL"
        elif command -v curl &>/dev/null; then
            curl -L -o "$DATA_DIR/$KERNEL_TARBALL" "$KERNEL_URL"
        else
            echo -e "${RED}Need wget or curl to download the kernel tarball.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}  Using cached tarball: $DATA_DIR/$KERNEL_TARBALL${NC}"
    fi

    echo -e "${YELLOW}  Extracting ${KERNEL_TARBALL}...${NC}"
    tar -xf "$DATA_DIR/$KERNEL_TARBALL" -C "$DATA_DIR"
    echo -e "${GREEN}  Extracted to $KERNEL_DIR${NC}"
}

ensure_kernel_config() {
    cd "$KERNEL_DIR"

    if [ ! -f .config ]; then
        echo -e "${YELLOW}  No .config found — creating minimal QEMU virtio config...${NC}"
        make defconfig > /dev/null
        ./scripts/config --enable BLK_DEV_INITRD
        ./scripts/config --enable DEVTMPFS
        ./scripts/config --enable DEVTMPFS_MOUNT
        ./scripts/config --enable PCI
        ./scripts/config --enable VIRTIO
        ./scripts/config --enable VIRTIO_PCI
        ./scripts/config --enable MODULES
        ./scripts/config --enable SERIAL_8250
        ./scripts/config --enable SERIAL_8250_CONSOLE
        ./scripts/config --enable TTY
        ./scripts/config --enable EXT4_FS
        make olddefconfig > /dev/null
    fi

    echo -e "${YELLOW}  Preparing kernel build headers (modules_prepare)...${NC}"
    make modules_prepare > /dev/null
    echo -e "${GREEN}  Kernel tree ready for out-of-tree module builds.${NC}"
}

build_kernel_image() {
    local variant="$1"   # novblk | builtin
    local output="$2"
    local config_cmd="$3"

    if [ -f "$output" ] && [ "$FORCE" -eq 0 ]; then
        echo -e "${GREEN}  $output already exists, skipping.${NC}"
        return
    fi

    echo -e "${YELLOW}  Building kernel (${variant})...${NC}"
    cd "$KERNEL_DIR"
    cp .config .config.setup_backup
    eval "$config_cmd"
    make olddefconfig > /dev/null
    make -j"$(nproc)" bzImage
    cp arch/x86/boot/bzImage "$output"
    mv .config.setup_backup .config
    echo -e "${GREEN}  Built $output${NC}"
}

build_kernels() {
    echo -e "${BLUE}[3/4] Building kernel images...${NC}"
    ensure_kernel_config

    # For loading out-of-tree vblk.ko (test_qemu.sh / SYSSPEC module test)
    build_kernel_image "novblk" "$KERNEL_NOVBLK" \
        './scripts/config --disable VIRTIO_BLK'

    # For built-in virtio-blk baseline (run_benchmark.sh)
    build_kernel_image "builtin" "$KERNEL_BUILTIN" \
        './scripts/config --enable BLK_DEV; ./scripts/config --set-val VIRTIO_BLK y'

    ln -sf "bzImage-${KERNEL_VERSION}-novblk" "$KERNEL_DEFAULT"
    echo -e "${GREEN}  Default test kernel: $KERNEL_DEFAULT -> novblk${NC}"
}

build_fio() {
    echo -e "${BLUE}[3/4] Building static fio...${NC}"

    if [ -f "$FIO_BIN" ] && [ "$FORCE" -eq 0 ]; then
        echo -e "${GREEN}  $FIO_BIN already exists, skipping.${NC}"
        return
    fi

    local fio_build_dir
    fio_build_dir="$(mktemp -d)"
    cd "$fio_build_dir"
    git clone --depth 1 https://github.com/axboe/fio.git . > /dev/null 2>&1
    LDFLAGS="-static" make -j"$(nproc)" > /dev/null 2>&1
    strip fio
    cp fio "$FIO_BIN"
    cd "$PROJECT_ROOT"
    rm -rf "$fio_build_dir"
    echo -e "${GREEN}  Built $FIO_BIN ($(du -h "$FIO_BIN" | cut -f1))${NC}"
}

print_summary() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${GREEN}  QEMU environment setup complete${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo "Kernel tree:  $KERNEL_DIR"
    [ -f "$KERNEL_NOVBLK" ] && echo "Test kernel:  $KERNEL_NOVBLK (symlink: $KERNEL_DEFAULT)"
    [ -f "$KERNEL_BUILTIN" ] && echo "Builtin kernel: $KERNEL_BUILTIN"
    [ -f "$FIO_BIN" ] && echo "fio binary:   $FIO_BIN"
    echo ""
    echo "Auto-generated at test time (not stored permanently):"
    echo "  data/test-disk.img, data/benchmark-disk.img"
    echo "  data/initramfs.cpio, data/initramfs_bench.cpio"
    echo ""
    echo "Next steps:"
    echo "  ./regen_virtio.sh build       # generate + compile vblk.ko"
    echo "  ./test_qemu.sh                # functional QEMU test"
    echo "  ./regen_virtio.sh benchmark   # fio performance comparison"
    echo ""
}

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  SYSSPEC QEMU Environment Setup${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

check_deps
fetch_kernel_tree

if [ "$BUILD_KERNELS" -eq 1 ] && [ "$BUILD_FIO" -eq 1 ]; then
    build_kernels
    echo -e "${BLUE}[4/4] Building benchmark tools...${NC}"
    build_fio
elif [ "$BUILD_KERNELS" -eq 1 ]; then
    build_kernels
    echo -e "${BLUE}[4/4] Skipping fio (use --fio or --all to build).${NC}"
elif [ "$BUILD_FIO" -eq 1 ]; then
    ensure_kernel_config
    echo -e "${BLUE}[3/4] Building benchmark tools...${NC}"
    build_fio
    echo -e "${BLUE}[4/4] Skipping kernel images (use --kernels or --all to build).${NC}"
else
    ensure_kernel_config
    echo -e "${BLUE}[3/4] Skipping kernel images (use --kernels or --all).${NC}"
    echo -e "${BLUE}[4/4] Skipping fio (use --fio or --all).${NC}"
fi

print_summary
