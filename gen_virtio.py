#!/usr/bin/env python3
"""
Virtio-blk driver generation pipeline using SYSSPEC.
Generates Linux kernel module code from .spec files.

Usage:
    uv run python gen_virtio.py          # generate code only
    uv run python gen_virtio.py build    # generate + compile kernel module
    uv run python gen_virtio.py test     # generate + compile + QEMU test
"""
import sys
import os
import argparse
import subprocess
from pathlib import Path

from utils import setup_logger, console
from tools.spec2code import spec2code

PROJECT_ROOT = Path(__file__).parent.resolve()
VIO_SPEC_DIR = PROJECT_ROOT / "sysspec" / "virtio-blk-spec"
VIO_GEN_DIR = PROJECT_ROOT / "sysspec" / "vio-blk-gen"


def generate_code(logger, max_workers=10):
    """Generate C code from virtio-blk spec files."""
    console.print("[bold blue]== Generating virtio-blk driver code ==[/]")
    spec2code(PROJECT_ROOT / "sysspec", logger, "virtio-blk",
              max_workers=max_workers, dst_name="vio-blk-gen")
    console.print("[bold green]Code generation complete.[/]")


def evolve_code(logger, max_workers=10):
    """Evolve existing virtio-blk code using optimized specs."""
    console.print("[bold blue]== Evolving virtio-blk driver code ==[/]")
    gen_dir = PROJECT_ROOT / "sysspec" / "vio-blk-gen"
    if not any(gen_dir.glob("*.c")):
        console.print("[bold yellow]No existing generated code found. Run 'generate' first.[/]")
        return
    spec2code(PROJECT_ROOT / "sysspec", logger, "evolve-virtio-blk",
              max_workers=max_workers, dst_name="vio-blk-gen")
    console.print("[bold green]Evolution complete.[/]")


def build_module():
    """Build the kernel module."""
    console.print("[bold blue]== Building virtio-blk kernel module ==[/]")
    kdir = str(PROJECT_ROOT / "data" / "linux-6.14.4")
    env = os.environ.copy()
    env["KDIR"] = kdir
    result = subprocess.run(
        ["make", "clean"], cwd=str(VIO_GEN_DIR), capture_output=True, text=True, env=env
    )
    result = subprocess.run(
        ["make"], cwd=str(VIO_GEN_DIR), capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        # Print stderr directly to avoid rich markup issues
        sys.stderr.write(f"Build failed:\n{result.stderr}\n")
        return False
    console.print("[bold green]Build successful.[/]")
    return True


def qemu_test():
    """Run QEMU test with the generated module."""
    console.print("[bold blue]== Running QEMU test ==[/]")
    # Check for test image
    test_img = PROJECT_ROOT / "data" / "test-rootfs.img"
    if not test_img.exists():
        console.print("[bold yellow]Test rootfs image not found. Skipping QEMU test.[/]")
        console.print(f"Create {test_img} to enable QEMU testing.")
        return True

    qemu_cmd = [
        "qemu-system-x86_64",
        "-kernel", "/boot/vmlinuz-$(uname -r)",
        "-append", "root=/dev/vda1 console=ttyS0",
        "-drive", f"file={test_img},format=raw,if=none,id=drv0",
        "-device", "virtio-blk-pci,drive=drv0",
        "-nographic", "-m", "512M",
        "-no-reboot",
    ]
    console.print(f"[dim]QEMU command: {' '.join(qemu_cmd)}[/]")
    console.print("[bold yellow]QEMU test requires manual setup. See docs/virtio-blk-test.md[/]")
    return True


def main():
    parser = argparse.ArgumentParser(description="Virtio-blk driver generation pipeline")
    parser.add_argument('action', nargs='?', default='generate',
                       choices=['generate', 'evolve', 'build', 'test'],
                       help='Action: generate (default), evolve, build, or test')
    parser.add_argument('--workers', type=int, default=10,
                       help='Max concurrent LLM workers (default: 10)')
    args = parser.parse_args()

    log_dir = PROJECT_ROOT / "log"
    logger = setup_logger(log_dir, "virtio-blk", to_console=True)

    # Check API key
    client_type = os.getenv("CLIENT", "google")
    if client_type == "google":
        if not os.getenv("GOOGLE_API_KEY"):
            console.print("[bold red]GOOGLE_API_KEY not set.[/]")
            sys.exit(1)
    elif not os.getenv("DEEPSEEK_API_KEY"):
        console.print("[bold red]DEEPSEEK_API_KEY not set.[/]")
        sys.exit(1)

    # Generate or evolve code
    if args.action == 'evolve':
        evolve_code(logger, max_workers=args.workers)
    else:
        generate_code(logger, max_workers=args.workers)

    if args.action in ('build', 'evolve', 'test'):
        if not build_module():
            sys.exit(1)

    if args.action == 'test':
        qemu_test()

    console.print("\n[bold green]Done![/]")


if __name__ == "__main__":
    main()
