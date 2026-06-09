#!/bin/bash
# SYSSPEC Virtio-Blk Performance Benchmark
# Compares standard (in-tree) virtio-blk vs SYSSPEC-generated vblk
# Both use the same kernel version (6.14.4) for a fair comparison.
# Uses fio for professional-grade I/O benchmarking.
#
# Usage: ./run_benchmark.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
DATA_DIR="$PROJECT_ROOT/data"
GEN_DIR="$PROJECT_ROOT/sysspec/vio-blk-gen"
CUSTOM_KERNEL_DIR="$DATA_DIR/linux-6.14.4"
KERNEL_BUILTIN="$DATA_DIR/bzImage-6.14.4-builtin"
KERNEL_NOVBLK="$DATA_DIR/bzImage-6.14.4-novblk"
DISK_IMG="$DATA_DIR/benchmark-disk.img"
BUSYBOX="/usr/bin/busybox"
FIO_BIN="$DATA_DIR/fio"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  SYSSPEC Virtio-Blk Performance Benchmark${NC}"
echo -e "${BLUE}  (fio, unified kernel: linux-6.14.4)${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# ───────────────────────────── Prerequisites ──────────────────────────────

if [ ! -f "$BUSYBOX" ]; then
    echo -e "${RED}ERROR: busybox not found. Install with: sudo apt install busybox${NC}"
    exit 1
fi

if [ ! -d "$CUSTOM_KERNEL_DIR" ]; then
    echo -e "${RED}ERROR: Kernel source not found at $CUSTOM_KERNEL_DIR${NC}"
    exit 1
fi

# Build static fio if not present
if [ ! -f "$FIO_BIN" ]; then
    echo -e "${YELLOW}Building static fio binary...${NC}"
    FIO_BUILD_DIR=$(mktemp -d)
    cd "$FIO_BUILD_DIR"
    git clone --depth 1 https://github.com/axboe/fio.git . > /dev/null 2>&1
    LDFLAGS="-static" make -j$(nproc) > /dev/null 2>&1
    strip fio
    cp fio "$FIO_BIN"
    cd "$SCRIPT_DIR"
    rm -rf "$FIO_BUILD_DIR"
    echo -e "${GREEN}  fio built: $FIO_BIN ($(du -h "$FIO_BIN" | cut -f1))${NC}"
fi

# Create test disk if needed
if [ ! -f "$DISK_IMG" ]; then
    echo -e "${YELLOW}Creating benchmark disk image (500MB)...${NC}"
    dd if=/dev/zero of="$DISK_IMG" bs=1M count=500 2>/dev/null
fi

# ─────────────────────────── [1/5] Build vblk.ko ──────────────────────────

echo -e "${YELLOW}[1/5] Building SYSSPEC vblk module...${NC}"
cd "$GEN_DIR"
KDIR="$CUSTOM_KERNEL_DIR" make clean > /dev/null 2>&1
KDIR="$CUSTOM_KERNEL_DIR" make > /dev/null 2>&1
echo -e "${GREEN}  vblk.ko built successfully.${NC}"

# ──────────────── [2/5] Build kernel with virtio_blk built-in ─────────────

if [ ! -f "$KERNEL_BUILTIN" ]; then
    echo -e "${YELLOW}[2/5] Building kernel 6.14.4 (CONFIG_VIRTIO_BLK=y)...${NC}"
    cd "$CUSTOM_KERNEL_DIR"
    cp .config .config.backup
    ./scripts/config --enable BLK_DEV
    ./scripts/config --set-val VIRTIO_BLK y
    make olddefconfig > /dev/null 2>&1
    make -j$(nproc) bzImage > /dev/null 2>&1
    cp arch/x86/boot/bzImage "$KERNEL_BUILTIN"
    cp .config.backup .config
    echo -e "${GREEN}  Builtin kernel built.${NC}"
else
    echo -e "${GREEN}[2/5] Builtin kernel already exists, skipping.${NC}"
fi

# ──────────────── [3/5] Build kernel without virtio_blk ───────────────────

if [ ! -f "$KERNEL_NOVBLK" ]; then
    echo -e "${YELLOW}[3/5] Building kernel 6.14.4 (no virtio_blk)...${NC}"
    cd "$CUSTOM_KERNEL_DIR"
    cp .config .config.backup
    ./scripts/config --disable VIRTIO_BLK
    make olddefconfig > /dev/null 2>&1
    make -j$(nproc) bzImage > /dev/null 2>&1
    cp arch/x86/boot/bzImage "$KERNEL_NOVBLK"
    cp .config.backup .config
    echo -e "${GREEN}  No-vblk kernel built.${NC}"
else
    echo -e "${GREEN}[3/5] No-vblk kernel already exists, skipping.${NC}"
fi

# ──────────────────── [4/5] Create initramfs ──────────────────────────────

echo -e "${YELLOW}[4/5] Creating initramfs (with fio)...${NC}"
INITRAMFS_DIR=$(mktemp -d)
mkdir -p "$INITRAMFS_DIR"/{bin,dev,proc,sys,lib/modules}

cp "$BUSYBOX" "$INITRAMFS_DIR/bin/busybox"
for cmd in sh ls cat mount umount insmod mkdir mknod echo grep dmesg sleep bc printf; do
    ln -s busybox "$INITRAMFS_DIR/bin/$cmd"
done

# Include fio binary
cp "$FIO_BIN" "$INITRAMFS_DIR/bin/fio"
chmod +x "$INITRAMFS_DIR/bin/fio"

# Include SYSSPEC-generated vblk module
cp "$GEN_DIR/vblk.ko" "$INITRAMFS_DIR/lib/modules/"

cat > "$INITRAMFS_DIR/init" << 'INIT'
#!/bin/sh
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

DRIVER_NAME="$1"

if [ "$DRIVER_NAME" = "vblk" ]; then
    insmod /lib/modules/vblk.ko
    sleep 1
fi

if [ ! -b /dev/vda ]; then
    echo "ERROR: /dev/vda not found"
    echo "RESULTS:0:0:0:0"
    exec /bin/sh
fi

FIO_COMMON="--filename=/dev/vda --direct=1 --ioengine=sync --group_reporting=1 --output-format=json --time_based --runtime=30s"
FIO_SIZE="100M"

# Extract a JSON field value by name from fio JSON output.
# Matches "field" : value lines (avoids bw_min, iops_stddev, etc.)
# Busybox-compatible: uses printf instead of echo to avoid escape sequence
# interpretation of fio JSON backslashes.
parse_json_field() {
    json="$1"
    field="$2"
    idx="${3:-1}"
    printf "%s\n" "$json" | grep "\"${field}\"" | head -n "$idx" | tail -n 1 | sed 's/.*: *//' | sed 's/[^0-9.]//g'
}

# fio JSON has sections: read, write, trim. For single-mode tests (read-only
# or write-only), the matching section is listed first. Use index 1 for read
# tests and index 2 for write tests.
idx_for_rw() {
    case "$1" in
        write|randwrite) echo 2 ;;
        *) echo 1 ;;
    esac
}

# Sequential read (1M block, 100M region)
SEQ_JSON=$(fio --name=seq_read $FIO_COMMON --rw=read --bs=1M --size=$FIO_SIZE 2>/dev/null)
SEQ_READ_BW=$(parse_json_field "$SEQ_JSON" "bw" $(idx_for_rw read))

# Sequential write (1M block, 100M region)
SEQ_JSON=$(fio --name=seq_write $FIO_COMMON --rw=write --bs=1M --size=$FIO_SIZE 2>/dev/null)
SEQ_WRITE_BW=$(parse_json_field "$SEQ_JSON" "bw" $(idx_for_rw write))

# 4K random read (100M region)
SEQ_JSON=$(fio --name=rnd_read $FIO_COMMON --rw=randread --bs=4k --size=$FIO_SIZE 2>/dev/null)
RND_READ_IOPS=$(parse_json_field "$SEQ_JSON" "iops" $(idx_for_rw randread))

# 4K random write (100M region)
SEQ_JSON=$(fio --name=rnd_write $FIO_COMMON --rw=randwrite --bs=4k --size=$FIO_SIZE 2>/dev/null)
RND_WRITE_IOPS=$(parse_json_field "$SEQ_JSON" "iops" $(idx_for_rw randwrite))

# Validate results
if [ -z "$SEQ_READ_BW" ] || [ -z "$SEQ_WRITE_BW" ] || [ -z "$RND_READ_IOPS" ] || [ -z "$RND_WRITE_IOPS" ]; then
    echo "ERROR: fio benchmark failed to produce valid results"
    echo "RESULTS:FAIL"
    exec /bin/sh
fi

# bw is in KB/s, convert to MB/s
SEQ_READ_MB=$(echo "scale=2; ${SEQ_READ_BW:-0} / 1024" | bc 2>/dev/null || echo "0")
SEQ_WRITE_MB=$(echo "scale=2; ${SEQ_WRITE_BW:-0} / 1024" | bc 2>/dev/null || echo "0")

echo "RESULTS:${SEQ_READ_MB}:${SEQ_WRITE_MB}:${RND_READ_IOPS:-0}:${RND_WRITE_IOPS:-0}"
INIT
chmod +x "$INITRAMFS_DIR/init"

cd "$CUSTOM_KERNEL_DIR"
./usr/gen_init_cpio <(cat <<EOF
dir /dev 0755 0 0
dir /bin 0755 0 0
dir /sbin 0755 0 0
dir /proc 0755 0 0
dir /sys 0755 0 0
dir /mnt 0755 0 0
dir /lib 0755 0 0
dir /lib/modules 0755 0 0
nod /dev/console 0600 0 0 c 5 1
nod /dev/null 0666 0 0 c 1 3
nod /dev/tty 0666 0 0 c 5 0
file /init $INITRAMFS_DIR/init 0755 0 0
file /bin/busybox $INITRAMFS_DIR/bin/busybox 0755 0 0
file /bin/fio $INITRAMFS_DIR/bin/fio 0755 0 0
slink /bin/sh busybox 0777 0 0
slink /bin/ls busybox 0777 0 0
slink /bin/cat busybox 0777 0 0
slink /bin/mount busybox 0777 0 0
slink /bin/umount busybox 0777 0 0
slink /bin/insmod busybox 0777 0 0
slink /bin/mkdir busybox 0777 0 0
slink /bin/mknod busybox 0777 0 0
slink /bin/echo busybox 0777 0 0
slink /bin/grep busybox 0777 0 0
slink /bin/dmesg busybox 0777 0 0
slink /bin/sleep busybox 0777 0 0
slink /bin/bc busybox 0777 0 0
slink /bin/printf busybox 0777 0 0
file /lib/modules/vblk.ko $INITRAMFS_DIR/lib/modules/vblk.ko 0644 0 0
EOF
) | gzip > "$DATA_DIR/initramfs_bench.cpio"
rm -rf "$INITRAMFS_DIR"
echo -e "${GREEN}  Initramfs created ($(du -h "$DATA_DIR/initramfs_bench.cpio" | cut -f1)).${NC}"

# ─────────────── [5/5] Run benchmarks ─────────────────────────────────────

# Auto-detect KVM and set timeout accordingly.
# Without KVM, QEMU uses TCG software emulation which is ~10-50x slower.
if [ -c /dev/kvm ]; then
    QEMU_TIMEOUT=300
    echo -e "${GREEN}  KVM available -- using hardware acceleration.${NC}"
else
    QEMU_TIMEOUT=900
    echo -e "${YELLOW}  No KVM -- using TCG emulation (slower). Timeout: ${QEMU_TIMEOUT}s.${NC}"
fi

QEMU_RETRIES=2

echo -e "${YELLOW}[5/5] Running fio benchmarks (kernel 6.14.4)...${NC}"
echo -e "${YELLOW}  Running standard (built-in) virtio-blk...${NC}"
BUILTIN_LOG="$DATA_DIR/qemu-builtin.log"
BUILTIN_OK=0
for _attempt in $(seq 1 $QEMU_RETRIES); do
    timeout $QEMU_TIMEOUT qemu-system-x86_64 \
        -kernel "$KERNEL_BUILTIN" \
        -initrd "$DATA_DIR/initramfs_bench.cpio" \
        -append "console=ttyS0 rdinit=/init builtin" \
        -drive file="$DISK_IMG",format=raw,if=none,id=drv0 \
        -device virtio-blk-pci,drive=drv0 \
        -nographic -m 512M -no-reboot > "$BUILTIN_LOG" 2>&1 || true
    if [ -s "$BUILTIN_LOG" ]; then
        BUILTIN_OK=1
        break
    fi
    echo -e "${YELLOW}  Retry $_attempt/$QEMU_RETRIES (QEMU produced no output)...${NC}"
    sleep 2
done
if [ "$BUILTIN_OK" -ne 1 ]; then
    echo -e "${RED}  Built-in virtio-blk: QEMU produced no output after $QEMU_RETRIES attempts.${NC}"
    echo -e "${RED}  Try running manually:${NC}"
    echo -e "${RED}    timeout $QEMU_TIMEOUT qemu-system-x86_64 -kernel $KERNEL_BUILTIN -initrd $DATA_DIR/initramfs_bench.cpio -append 'console=ttyS0 rdinit=/init builtin' -drive file=$DISK_IMG,format=raw,if=none,id=drv0 -device virtio-blk-pci,drive=drv0 -nographic -m 512M -no-reboot${NC}"
    exit 1
fi
BUILTIN_RAW=$(grep "^RESULTS:" "$BUILTIN_LOG" | tail -1 || echo "RESULTS:FAIL")

if echo "$BUILTIN_RAW" | grep -q "FAIL"; then
    echo -e "${RED}  Built-in virtio-blk benchmark FAILED!${NC}"
    echo -e "${RED}  Full log: $BUILTIN_LOG${NC}"
    exit 1
fi
BUILTIN_SEQ_READ=$(echo "$BUILTIN_RAW" | cut -d: -f2)
BUILTIN_SEQ_WRITE=$(echo "$BUILTIN_RAW" | cut -d: -f3)
BUILTIN_RND_READ=$(echo "$BUILTIN_RAW" | cut -d: -f4)
BUILTIN_RND_WRITE=$(echo "$BUILTIN_RAW" | cut -d: -f5)
echo -e "${GREEN}  Built-in: SeqR=${BUILTIN_SEQ_READ}MB/s SeqW=${BUILTIN_SEQ_WRITE}MB/s RndR=${BUILTIN_RND_READ}IOPS RndW=${BUILTIN_RND_WRITE}IOPS${NC}"

echo -e "${YELLOW}  Running SYSSPEC vblk module...${NC}"
VBLK_LOG="$DATA_DIR/qemu-vblk.log"
VBLK_OK=0
for _attempt in $(seq 1 $QEMU_RETRIES); do
    timeout $QEMU_TIMEOUT qemu-system-x86_64 \
        -kernel "$KERNEL_NOVBLK" \
        -initrd "$DATA_DIR/initramfs_bench.cpio" \
        -append "console=ttyS0 rdinit=/init vblk" \
        -drive file="$DISK_IMG",format=raw,if=none,id=drv0 \
        -device virtio-blk-pci,drive=drv0 \
        -nographic -m 512M -no-reboot > "$VBLK_LOG" 2>&1 || true
    if [ -s "$VBLK_LOG" ]; then
        VBLK_OK=1
        break
    fi
    echo -e "${YELLOW}  Retry $_attempt/$QEMU_RETRIES (QEMU produced no output)...${NC}"
    sleep 2
done
if [ "$VBLK_OK" -ne 1 ]; then
    echo -e "${RED}  SYSSPEC vblk: QEMU produced no output after $QEMU_RETRIES attempts.${NC}"
    echo -e "${RED}  Log: $VBLK_LOG${NC}"
    exit 1
fi
VBLK_RAW=$(grep "^RESULTS:" "$VBLK_LOG" | tail -1 || echo "RESULTS:FAIL")

if echo "$VBLK_RAW" | grep -q "FAIL"; then
    echo -e "${RED}  SYSSPEC vblk benchmark FAILED!${NC}"
    echo -e "${RED}  Full log: $VBLK_LOG${NC}"
    exit 1
fi
VBLK_SEQ_READ=$(echo "$VBLK_RAW" | cut -d: -f2)
VBLK_SEQ_WRITE=$(echo "$VBLK_RAW" | cut -d: -f3)
VBLK_RND_READ=$(echo "$VBLK_RAW" | cut -d: -f4)
VBLK_RND_WRITE=$(echo "$VBLK_RAW" | cut -d: -f5)
echo -e "${GREEN}  vblk:     SeqR=${VBLK_SEQ_READ}MB/s SeqW=${VBLK_SEQ_WRITE}MB/s RndR=${VBLK_RND_READ}IOPS RndW=${VBLK_RND_WRITE}IOPS${NC}"

# ──────────────────── Generate comparison chart ───────────────────────────

echo ""
echo -e "${YELLOW}Generating performance comparison chart...${NC}"

cat > /tmp/plot_benchmark.py << PYTHON
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Values are already in proper units from fio (MB/s and IOPS)
builtin = [float(x) for x in sys.argv[1:5]]
vblk = [float(x) for x in sys.argv[5:9]]

categories = ['Seq Read\n(MB/s)', 'Seq Write\n(MB/s)', '4K Rand Read\n(IOPS)', '4K Rand Write\n(IOPS)']

fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(categories))
width = 0.35

bars1 = ax.bar(x - width/2, builtin, width, label='Standard virtio-blk (kernel 6.14.4)', color='#2196F3')
bars2 = ax.bar(x + width/2, vblk, width, label='SYSSPEC vblk (kernel 6.14.4)', color='#4CAF50')

ax.set_ylabel('Performance')
ax.set_title('Virtio-blk Driver Performance Comparison (fio, Same Kernel)')
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.legend()

def autolabel(bars):
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

autolabel(bars1)
autolabel(bars2)

plt.tight_layout()
output_path = sys.argv[9] if len(sys.argv) > 9 else 'result/vblk_benchmark.png'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Chart saved to {output_path}")
PYTHON

# Validate all values are non-empty before plotting
for val_name in BUILTIN_SEQ_READ BUILTIN_SEQ_WRITE BUILTIN_RND_READ BUILTIN_RND_WRITE \
                VBLK_SEQ_READ VBLK_SEQ_WRITE VBLK_RND_READ VBLK_RND_WRITE; do
    eval val=\$$val_name
    if [ -z "$val" ]; then
        echo -e "${RED}ERROR: $val_name is empty. Check QEMU logs:${NC}"
        echo -e "${RED}  $DATA_DIR/qemu-builtin.log${NC}"
        echo -e "${RED}  $DATA_DIR/qemu-vblk.log${NC}"
        exit 1
    fi
done

mkdir -p "$PROJECT_ROOT/result"
python3 /tmp/plot_benchmark.py \
    "$BUILTIN_SEQ_READ" "$BUILTIN_SEQ_WRITE" "$BUILTIN_RND_READ" "$BUILTIN_RND_WRITE" \
    "$VBLK_SEQ_READ" "$VBLK_SEQ_WRITE" "$VBLK_RND_READ" "$VBLK_RND_WRITE" \
    "$PROJECT_ROOT/result/vblk_benchmark.png"

# ──────────────────── Print summary ───────────────────────────────────────

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  Performance Comparison Summary${NC}"
echo -e "${BLUE}  Benchmark: fio | Kernel: linux-6.14.4${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Round IOPS to integers
BUILTIN_RND_READ=$(printf "%.0f" "$BUILTIN_RND_READ" 2>/dev/null || echo "0")
BUILTIN_RND_WRITE=$(printf "%.0f" "$BUILTIN_RND_WRITE" 2>/dev/null || echo "0")
VBLK_RND_READ=$(printf "%.0f" "$VBLK_RND_READ" 2>/dev/null || echo "0")
VBLK_RND_WRITE=$(printf "%.0f" "$VBLK_RND_WRITE" 2>/dev/null || echo "0")

# Compute ratios (builtin / vblk)
SEQ_READ_RATIO=$(echo "scale=2; $BUILTIN_SEQ_READ / $VBLK_SEQ_READ" | bc -l 2>/dev/null || echo "0")
SEQ_WRITE_RATIO=$(echo "scale=2; $BUILTIN_SEQ_WRITE / $VBLK_SEQ_WRITE" | bc -l 2>/dev/null || echo "0")
RND_READ_RATIO=$(echo "scale=2; $BUILTIN_RND_READ / $VBLK_RND_READ" | bc -l 2>/dev/null || echo "0")
RND_WRITE_RATIO=$(echo "scale=2; $BUILTIN_RND_WRITE / $VBLK_RND_WRITE" | bc -l 2>/dev/null || echo "0")

printf "%-20s %15s %15s %10s\n" "Test" "Standard" "SYSSPEC vblk" "Ratio"
printf "%-20s %15s %15s %10s\n" "----" "--------" "------------" "-----"
printf "%-20s %10s MB/s %10s MB/s %9sx\n" "Seq Read" "$BUILTIN_SEQ_READ" "$VBLK_SEQ_READ" "$SEQ_READ_RATIO"
printf "%-20s %10s MB/s %10s MB/s %9sx\n" "Seq Write" "$BUILTIN_SEQ_WRITE" "$VBLK_SEQ_WRITE" "$SEQ_WRITE_RATIO"
printf "%-20s %10s IOPS %10s IOPS %9sx\n" "4K Rand Read" "$BUILTIN_RND_READ" "$VBLK_RND_READ" "$RND_READ_RATIO"
printf "%-20s %10s IOPS %10s IOPS %9sx\n" "4K Rand Write" "$BUILTIN_RND_WRITE" "$VBLK_RND_WRITE" "$RND_WRITE_RATIO"
echo ""
echo -e "${GREEN}Chart saved to: $PROJECT_ROOT/result/vblk_benchmark.png${NC}"
echo -e "${BLUE}=========================================${NC}"
