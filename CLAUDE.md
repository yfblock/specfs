# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SpecFS is an artifact for the FAST'26 paper "Sharpen the Spec, Cut the Code: A Case for Generative File System with SYSSPEC". It uses LLMs (Google Gemini or DeepSeek) to automatically generate a FUSE-based userspace filesystem (AtomFS) from formal specifications written in Hoare Logic style.

Two generation modes for AtomFS:
- **`gen`**: Generate C code from `.spec` files directly
- **`evolve`**: Improve existing code given an optimized specification

**Virtio-blk extension** (`gen_virtio.py`): Extends the SYSSPEC methodology to generate a Linux kernel virtio-blk block device driver from formal specifications. Targets QEMU virtio-blk PCI devices.

## Commands

### Environment Setup
```bash
cp .env.example .env   # then edit with API keys and MOUNT_POINT
uv sync                # install Python dependencies (requires Python >= 3.12)
```

### Generation Pipeline
```bash
uv run python gen.py gen       # fresh generation from specs (~15-20 min with Google, ~30 min with DeepSeek)
uv run python gen.py evolve    # evolutionary improvement mode
```

### Evaluation (reproduces paper results)
```bash
uv run python eval.py          # runs all benchmarks, generates plots in result/
```

### Build the Filesystem (standalone, after code is generated)
```bash
cd sysspec/genfs
make clean && make               # release build -> atomfs-fuse
make atomfs-fuse-debug           # debug build with -g -DDEBUG
```

### Build Benchmark Tools
```bash
cd tools
make                             # builds largefile, smallfile, prealloc_test, rbtree_test
```

### Virtio-blk Driver Generation
```bash
./regen_virtio.sh                        # generate + compile kernel module
./regen_virtio.sh benchmark              # generate + compile + run fio benchmark
./regen_virtio.sh evolve                 # evolve with optimized specs + compile
./regen_virtio.sh evolve-benchmark       # evolve + compile + benchmark
./regen_virtio.sh clean                  # clean generated files
# QEMU test (requires kernel image):
./test_qemu.sh                           # interactive QEMU test with vblk.ko
# Benchmark only (after building):
./run_benchmark.sh                       # fio benchmark: standard vs SYSSPEC vblk
# Manual kernel module build:
cd sysspec/vio-blk-gen && make           # build vblk.ko kernel module
```

### Mount/Run AtomFS
```bash
./sysspec/genfs/atomfs-fuse [-n] <device> <mount_point>   # -n = create new filesystem
```

## Architecture

### Pipeline Flow
```
sysspec/specfs/*.spec  -->  LLM (Gemini/DeepSeek)  -->  sysspec/genfs/*.c  -->  gcc+FUSE  -->  atomfs-fuse

sysspec/virtio-blk-spec/*.spec  -->  LLM  -->  sysspec/vio-blk-gen/*.c  -->  kbuild  -->  vblk.ko
```

The generation loop in `gen.py` retries until compile+test passes: `spec2code()` → `run_compile_and_test()` → repeat on failure.

### Two-Layer Spec System

**Specifications** (`sysspec/specfs/`): `.spec` files define each function with four sections — `[PROMPT]` (overall requirement), `[RELY]` (dependencies from other modules), `[GUARANTEE]` (function signature), `[SPECIFICATION]` (Hoare Logic pre/post-conditions). `.header` files define shared types and includes for a module.

**Generated code** (`sysspec/genfs/`): Each `.spec` produces one `.c` file. Headers are auto-generated from `.header` files. `atomfs-fuse.c`, `mcs.c`, `mcs.h`, and `Makefile` are hand-provided boilerplate.

**Evolution specs** (`sysspec/evolvefs/`): Optimized specifications for the `evolve` mode, paired with the existing generated code.

### Module Dependency Hierarchy (bottom-up)

**AtomFS** (`sysspec/specfs/` → `sysspec/genfs/`):
```
util          -- malloc_*, free_*, lock, hash, path splitting
file          -- file_allocate, file_read, file_write, file_clear  (depends: util)
inode         -- inode_find, inode_insert, inode_delete, ...       (depends: util, file)
path          -- locate, locate_hold                                (depends: inode)
interface-util -- check_del, check_ins, ...                         (depends: inode)
interface     -- atomfs_open, atomfs_read, atomfs_write, ...        (depends: all above)
```

**Virtio-blk** (`sysspec/virtio-blk-spec/` → `sysspec/vio-blk-gen/`):
```
util          -- vring_alloc_desc, vring_free_desc, vring_init, bitmap_alloc/free
virtqueue     -- vq_create, vq_add_buf, vq_kick, vq_get_buf, vq_enable/disable_irq
virtio-core   -- dev_reset, dev_negotiate, dev_setup_vqs, dev_read_config
virtio-blk    -- blk_req_build, blk_submit, blk_done
driver        -- blkdev_init, blkdev_exit, blk_request_fn
```
Hand-written: `vblk_mod.c` (PCI driver skeleton), `hw_ops.h` (MMIO/DMA/barrier primitives), `Makefile` (kbuild).

### Key Data Structures (in `sysspec/genfs/common.h`)

- `struct inode` — core filesystem node with mutex, MCS lock, mode, size, and pointer to either `dirtb` (directory) or `indextb` (file data)
- `struct indextb` — maps 8192 logical pages to physical page pointers (max 32MB files)
- `struct dirtb` — 512-bucket hash table of `entry` linked lists for directory contents
- `mcs_mutex_t` / `mcs_node_t` — MCS queue-based spinlock for concurrent access

### LLM Code Generation (`tools/gencode.py`, `tools/spec2code.py`)

- `spec2code.py` orchestrates parallel generation: reads all `.spec`/`.header` files, spawns threads (configurable via `MAX_WORKERS`), calls LLM per spec
- `gencode.py` handles LLM interaction. Two paths:
  - **Simple mode**: single LLM call per spec (when no "Refine Prompt" in spec)
  - **Workflow mode**: iterative CodeGenerator + SpecEvaluator loop (up to 8 rounds). The evaluator checks generated code against spec, provides modification suggestions if not matching, and the code is refined in the next round
- Header files are converted to C headers with include guards locally (no LLM needed)

### Testing (`tests/`)

All tests are integration-level — no unit tests. `test_specfs.py` compiles AtomFS, mounts it via FUSE, runs workloads (xv6 compile, QEMU copy, largefile/smallfile benchmarks including concurrency), then unmounts. Performance tests (`test_inline_data.py`, `test_pre_alloc.py`, `test_rbtree.py`, `test_block.py`) measure block counts and I/O metrics for optimization variants in `eval/`.

### Configuration (`.env`)

- `CLIENT` — `google` (Gemini, recommended) or `deepseek`
- `GOOGLE_API_KEY` / `DEEPSEEK_API_KEY` — API key for selected client
- `MOUNT_POINT` — where AtomFS gets mounted for testing
- `MAX_WORKERS` — concurrent LLM API requests (default 10, recommend 5 due to rate limits)
