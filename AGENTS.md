# Repository Guidelines

## Project Structure & Module Organization

SpecFS is an artifact for the FAST'26 paper on generative filesystems. It uses LLMs to generate a FUSE-based userspace filesystem (AtomFS) and a virtio-blk kernel driver from formal specifications.

```
.
├── gen.py / gen_virtio.py   # Main entry points for generation pipelines
├── eval.py                  # Full evaluation runner (benchmarks + plots)
├── utils.py                 # Shared Python utilities
├── sysspec/
│   ├── specfs/              # Formal specifications (.spec, .header files)
│   ├── genfs/               # LLM-generated C code + Makefile (output)
│   ├── evolvefs/            # Optimized specs for evolution mode
│   └── virtio-blk-spec/     # Virtio-blk specifications
├── tests/                   # Integration tests (FUSE mount, benchmarks)
├── tools/                   # LLM orchestration (spec2code.py, gencode.py) + benchmark C binaries
├── plot/                    # Plotting scripts for paper figures
├── eval/                    # Pre-instrumented evaluation variants
└── result/                  # Generated plots and benchmark outputs
```

## Build, Test, and Development Commands

Install dependencies (requires Python >= 3.12):
```bash
uv sync
```

Generate filesystem from specifications:
```bash
uv run python gen.py gen          # ~15-20 min with Google Gemini
uv run python gen.py evolve       # evolve mode with optimized specs
```

Run full evaluation (reproduces paper results):
```bash
uv run python eval.py
```

Build the filesystem standalone (after generation):
```bash
cd sysspec/genfs && make                # release build
cd sysspec/genfs && make atomfs-fuse-debug  # debug build
```

Build benchmark tools:
```bash
cd tools && make
```

Virtio-blk driver:
```bash
./regen_virtio.sh benchmark       # generate + compile + fio benchmark
```

## Coding Style & Naming Conventions

- Python: 4-space indentation, no enforced linter. Follow existing patterns in `gen.py` and `eval.py`.
- C (generated and boilerplate): 4-space indentation, `gcc` with `-Wall -O2`. Module names use `lowercase` (e.g., `inode.c`, `file.c`).
- Specifications: `.spec` files use four sections — `[PROMPT]`, `[RELY]`, `[GUARANTEE]`, `[SPECIFICATION]`. `.header` files define shared types and includes.
- Shell scripts: lowercase with underscores for filenames.

## Testing Guidelines

All tests are integration-level; there is no unit test suite. Tests mount AtomFS via FUSE, run workloads (compile, I/O benchmarks), and validate correctness. Run them as part of the generation or evaluation pipeline rather than standalone:

```bash
uv run python eval.py    # runs all test+benchmark workflows
```

Individual test modules live under `tests/` (e.g., `test_specfs.py`, `test_rbtree.py`).

## Commit & Pull Request Guidelines

- The repository has a single initial commit (`repo: init`). Use short, imperative subject lines (e.g., `fix: handle edge case in inode lookup`).
- Reference related paper sections or evaluation results in commit bodies when relevant.
- Pull requests should describe the change, link any related issues, and include benchmark results or screenshots if the change affects evaluation output.

## Configuration

Copy `.env.example` to `.env` and set `CLIENT`, the corresponding API key (`GOOGLE_API_KEY` or `DEEPSEEK_API_KEY`), `MOUNT_POINT`, and `MAX_WORKERS`. Google Gemini is the recommended LLM backend. See `README.md` for full variable descriptions.
