#!/bin/bash
# Test script for SYSSPEC-generated virtio-blk driver
# Usage: ./test_qemu.sh [kernel_image]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
GEN_DIR="$SCRIPT_DIR/sysspec/vio-blk-gen"
MODULE="$GEN_DIR/vblk.ko"
DISK_IMG="$DATA_DIR/test-disk.img"
KERNEL="${1:-$DATA_DIR/bzImage}"

# Check prerequisites
if [ ! -f "$KERNEL" ]; then
    echo "ERROR: Kernel image not found at $KERNEL"
    echo "Please provide a kernel image:"
    echo "  $0 /path/to/bzImage"
    echo ""
    echo "Or copy the host kernel:"
    echo "  sudo cp /boot/vmlinuz-$(uname -r) $DATA_DIR/bzImage"
    exit 1
fi

if [ ! -f "$MODULE" ]; then
    echo "ERROR: Module not found at $MODULE"
    echo "Please build the module first:"
    echo "  ./regen_virtio.sh build"
    exit 1
fi

if [ ! -f "$DISK_IMG" ]; then
    echo "Creating test disk image..."
    dd if=/dev/zero of="$DISK_IMG" bs=1M count=100
fi

# Create initramfs with module
echo "Creating initramfs with virtio-blk module..."
INITRAMFS_DIR=$(mktemp -d)
mkdir -p "$INITRAMFS_DIR"/{bin,lib/modules,proc,sys,dev,mnt}

# Copy busybox or sh
if command -v busybox &>/dev/null; then
    cp "$(command -v busybox)" "$INITRAMFS_DIR/bin/"
    cd "$INITRAMFS_DIR/bin" && for cmd in sh ls cat mount umount insmod modprobe; do
        ln -sf busybox $cmd
    done
    cd -
else
    cp /bin/sh "$INITRAMFS_DIR/bin/" 2>/dev/null || true
fi

# Copy module
cp "$MODULE" "$INITRAMFS_DIR/lib/modules/"

# Create init script
cat > "$INITRAMFS_DIR/init" << 'INIT_SCRIPT'
#!/bin/sh
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

echo "=== SYSSPEC Virtio-Blk Test ==="
echo "Loading virtio-blk module..."
insmod /lib/modules/vblk.ko

echo "Checking for virtio-blk devices..."
ls -la /dev/vd* 2>/dev/null || echo "No /dev/vd* devices found"

echo "Checking dmesg for virtio-blk messages..."
dmesg | grep -i virtio | tail -10

echo "Dropping to shell..."
exec /bin/sh
INIT_SCRIPT
chmod +x "$INITRAMFS_DIR/init"

# Create initramfs
cd "$INITRAMFS_DIR"
find . | cpio -o -H newc 2>/dev/null | gzip > "$DATA_DIR/initramfs.cpio"
cd -

echo ""
echo "=== QEMU Test Command ==="
echo "qemu-system-x86_64 \\"
echo "  -kernel $KERNEL \\"
echo "  -initrd $DATA_DIR/initramfs.cpio \\"
echo "  -append \"console=ttyS0 rdinit=/init\" \\"
echo "  -drive file=$DISK_IMG,format=raw,if=none,id=drv0 \\"
echo "  -device virtio-blk-pci,drive=drv0 \\"
echo "  -nographic -m 512M"
echo ""
echo "Running QEMU..."
echo ""

qemu-system-x86_64 \
  -kernel "$KERNEL" \
  -initrd "$DATA_DIR/initramfs.cpio" \
  -append "console=ttyS0 rdinit=/init" \
  -drive file="$DISK_IMG",format=raw,if=none,id=drv0 \
  -device virtio-blk-pci,drive=drv0 \
  -nographic -m 512M \
  -no-reboot

echo ""
echo "=== Test Complete ==="
