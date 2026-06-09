#!/bin/bash
# Functional QEMU test for SYSSPEC-generated uart16550 driver on COM2 (0x2f8).
#
# Uses kernel param 8250.nr_uarts=1 so built-in 8250 leaves COM2 free.
# SYSSPEC module registers /dev/ttySY0 on the second ISA serial port.
#
# Usage: ./test_uart_qemu.sh [kernel_image]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
GEN_DIR="$SCRIPT_DIR/sysspec/uart16550-gen"
MODULE="$GEN_DIR/uart16550.ko"
KERNEL="${1:-$DATA_DIR/bzImage-6.14.4-novblk}"
CHAR_LOG="$DATA_DIR/qemu-uart.log"
COM2_OUT="$DATA_DIR/uart-com2.out"

if [ ! -f "$KERNEL" ]; then
    KERNEL="$DATA_DIR/bzImage"
fi

if [ ! -f "$KERNEL" ]; then
    echo "ERROR: Kernel image not found."
    echo "Run: ./scripts/setup-qemu-env.sh --kernels"
    exit 1
fi

if [ ! -f "$MODULE" ]; then
    echo "ERROR: Module not found at $MODULE"
    echo "Run: ./regen_uart16550.sh build"
    exit 1
fi

echo "Creating initramfs with uart16550 module..."
INITRAMFS_DIR=$(mktemp -d)
mkdir -p "$INITRAMFS_DIR"/{bin,lib/modules,proc,sys,dev}

if command -v busybox &>/dev/null; then
    cp "$(command -v busybox)" "$INITRAMFS_DIR/bin/"
    (
        cd "$INITRAMFS_DIR/bin"
        for cmd in sh ls cat mount umount insmod echo dmesg stty; do
            ln -sf busybox "$cmd"
        done
    )
else
    cp /bin/sh "$INITRAMFS_DIR/bin/" 2>/dev/null || true
fi

cp "$MODULE" "$INITRAMFS_DIR/lib/modules/"

cat > "$INITRAMFS_DIR/init" << 'INIT_SCRIPT'
#!/bin/sh
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

echo "=== SYSSPEC UART16550 Test ==="
echo "Loading uart16550 module on COM2 (0x2f8, irq 3)..."
insmod /lib/modules/uart16550.ko iobase=0x2f8 irq=3 || insmod /lib/modules/uart16550.ko

echo "TTY devices:"
ls -la /dev/ttySY* 2>/dev/null || echo "No /dev/ttySY* devices found"

echo "Driver messages:"
dmesg | grep -iE 'uart16550|ttySY' | tail -10

if [ -c /dev/ttySY0 ]; then
    echo "SYSSPEC-UART-OK" > /dev/ttySY0 &
    echo "Wrote test string to /dev/ttySY0"
else
    echo "ERROR: /dev/ttySY0 not present"
fi

echo "RESULT:UART_TEST_DONE"
sleep 1
exec /bin/sh
INIT_SCRIPT
chmod +x "$INITRAMFS_DIR/init"

(
    cd "$INITRAMFS_DIR"
    find . | cpio -o -H newc 2>/dev/null | gzip > "$DATA_DIR/initramfs_uart.cpio"
)

rm -f "$COM2_OUT"
echo "Running QEMU (COM2 at 0x2f8, log: $CHAR_LOG)..."
timeout 45 qemu-system-x86_64 \
    -display none \
    -monitor none \
    -chardev file,id=con,path="$CHAR_LOG",append=on \
    -serial chardev:con \
    -chardev file,id=uartcom2,path="$COM2_OUT",append=on \
    -kernel "$KERNEL" \
    -initrd "$DATA_DIR/initramfs_uart.cpio" \
    -append "console=ttyS0 8250.nr_uarts=1 rdinit=/init" \
    -m 512M -no-reboot 2>/dev/null || true

if grep -q "uart16550-sysspec: registered" "$CHAR_LOG" && \
   grep -qE 'ttySY0|/dev/ttySY0' "$CHAR_LOG"; then
    echo "=== UART test PASSED ==="
    grep -E 'uart16550-sysspec|ttySY|Wrote test string' "$CHAR_LOG" | tail -5 || true
    if [ -f "$COM2_OUT" ] && grep -q "SYSSPEC-UART-OK" "$COM2_OUT"; then
        echo "COM2 output captured: $(cat "$COM2_OUT")"
    fi
    exit 0
fi

echo "=== UART test FAILED ==="
tail -30 "$CHAR_LOG"
exit 1
