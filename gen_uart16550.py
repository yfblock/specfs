#!/usr/bin/env python3
"""
8250/16550 UART driver generation pipeline using SYSSPEC.
Generates Linux kernel module code from .spec files.

Usage:
    uv run python gen_uart16550.py          # generate code only
    uv run python gen_uart16550.py build    # generate + compile kernel module
    uv run python gen_uart16550.py test     # generate + compile + QEMU test
"""
import sys
import os
import argparse
import subprocess
from pathlib import Path

from utils import setup_logger, console
from tools.spec2code import spec2code

PROJECT_ROOT = Path(__file__).parent.resolve()
UART_GEN_DIR = PROJECT_ROOT / "sysspec" / "uart16550-gen"


def generate_code(logger, max_workers=10):
    """Generate C code from uart16550 spec files."""
    console.print("[bold blue]== Generating uart16550 driver code ==[/]")
    spec2code(PROJECT_ROOT / "sysspec", logger, "uart16550",
              max_workers=max_workers, dst_name="uart16550-gen")
    console.print("[bold green]Code generation complete.[/]")


def evolve_code(logger, max_workers=10):
    """Evolve existing uart16550 code using optimized specs."""
    console.print("[bold blue]== Evolving uart16550 driver code ==[/]")
    gen_dir = UART_GEN_DIR
    if not any(gen_dir.glob("uart/*.c")):
        console.print("[bold yellow]No existing generated code found. Run 'generate' first.[/]")
        return
    spec2code(PROJECT_ROOT / "sysspec", logger, "evolve-uart16550",
              max_workers=max_workers, dst_name="uart16550-gen")
    console.print("[bold green]Evolution complete.[/]")


def build_module():
    """Build the kernel module."""
    console.print("[bold blue]== Building uart16550 kernel module ==[/]")
    kdir = str(PROJECT_ROOT / "data" / "linux-6.14.4")
    env = os.environ.copy()
    env["KDIR"] = kdir
    result = subprocess.run(
        ["make", "clean"], cwd=str(UART_GEN_DIR), capture_output=True, text=True, env=env
    )
    result = subprocess.run(
        ["make"], cwd=str(UART_GEN_DIR), capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        sys.stderr.write(f"Build failed:\n{result.stderr}\n")
        if result.stdout:
            sys.stderr.write(result.stdout)
        return False
    console.print("[bold green]Build successful.[/]")
    return True


def qemu_test():
    """Run QEMU functional test."""
    console.print("[bold blue]== Running UART QEMU test ==[/]")
    script = PROJECT_ROOT / "test_uart_qemu.sh"
    if not script.exists():
        console.print("[bold yellow]test_uart_qemu.sh not found. Skipping.[/]")
        return True
    result = subprocess.run([str(script)], cwd=str(PROJECT_ROOT))
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="UART 16550 driver generation pipeline")
    parser.add_argument('action', nargs='?', default='generate',
                       choices=['generate', 'evolve', 'build', 'test'],
                       help='Action: generate (default), evolve, build, or test')
    parser.add_argument('--workers', type=int, default=10,
                       help='Max concurrent LLM workers (default: 10)')
    args = parser.parse_args()

    log_dir = PROJECT_ROOT / "log"
    logger = setup_logger(log_dir, "uart16550", to_console=True)

    client_type = os.getenv("CLIENT", "google")
    if client_type == "google":
        if not os.getenv("GOOGLE_API_KEY"):
            console.print("[bold red]GOOGLE_API_KEY not set.[/]")
            sys.exit(1)
    elif not os.getenv("DEEPSEEK_API_KEY"):
        console.print("[bold red]DEEPSEEK_API_KEY not set.[/]")
        sys.exit(1)

    if args.action == 'evolve':
        evolve_code(logger, max_workers=args.workers)
    else:
        generate_code(logger, max_workers=args.workers)

    if args.action in ('build', 'evolve', 'test'):
        if not build_module():
            sys.exit(1)

    if args.action == 'test':
        if not qemu_test():
            sys.exit(1)

    console.print("\n[bold green]Done![/]")


if __name__ == "__main__":
    main()
