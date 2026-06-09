import os
import sys
from logging import Logger
from pathlib import Path
from openai import OpenAI
import concurrent.futures
import threading
import functools

from tools.gencode import generate_code, evolve_code
from utils import ProgressTracker, setup_logger

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def generate_header_file(file_name, header_content):
    lines = header_content.strip().split('\n')
    if len(lines) < 2:
        return header_content
    
    STD_LIBS = {
        "assert", "complex", "ctype", "errno", "float", "inttypes",
        "limits", "locale", "math", "setjmp", "signal", "stdarg",
        "stdbool", "stddef", "stdint", "stdio", "stdlib", "string",
        "time", "uchar", "wchar", "wctype", "unistd", "sys/syscall"
    }
    # Treat linux/*, asm/*, uapi/* as system headers (kernel headers)
    KERNEL_HEADER_PREFIXES = ("linux/", "asm/", "uapi/", "uapi/linux/")

    includes_line = lines[0]
    includes = [include.strip() for include in includes_line.split(',')]
    
    include_statements = []
    for include in includes:
        if not include:
            continue
        if include in STD_LIBS or any(include.startswith(p) for p in KERNEL_HEADER_PREFIXES):
            include_statements.append(f'#include <{include}.h>')
        else:
            include_statements.append(f'#include "{include}.h"')
    
    result = '\n'.join(include_statements)
    if len(lines) > 1:
        remaining_content = '\n'.join(lines[1:])
        result += '\n\n' + remaining_content
    
    guard_name = '_' + file_name.upper().replace('-', '_').replace('.', '_') + '_H'
    header_guard_start = f"#ifndef {guard_name}\n#define {guard_name}\n\n"
    header_guard_end = f"\n#endif // {guard_name}"
    
    return header_guard_start + result + header_guard_end

def generate_c_file(spec_file_info, stats_lock, stats, logger, tracker: ProgressTracker):
    file_path, relative_path, output_file, spec_content, orig_code, orig_spec = spec_file_info
    
    try:
        client_type = os.getenv("CLIENT", "deepseek")
        if client_type == "google":
            from google import genai
            client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        else:
            client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com/v1"
            )
        use_workflow = "Refine Prompt" in spec_content
        
        log_filename = str(relative_path).replace('/', '_').replace('\\', '_').replace('.spec', '')
        # Use unified setup_logger, no console output for individual files
        file_logger = setup_logger(PROJECT_ROOT / "log", log_filename, to_console=False)

        if orig_code and orig_spec:
            api_output = evolve_code(client, spec_content, orig_code, orig_spec, logger=file_logger, file_name=file_path.name)
        else:
            api_output = generate_code(client, spec_content, use_workflow=use_workflow, logger=file_logger, file_name=file_path.name)
        
        if api_output is None:
            with stats_lock:
                stats['spec_errors'] += 1
            return

        cleaned_output = api_output
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_output or api_output)
        
        tracker.update(str(relative_path))

        file_logger.debug(f"Generated {output_file} from {file_path}")
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        with stats_lock:
            stats['spec_errors'] += 1


def get_files_to_process(src_path: Path, dst_path: Path):
    spec_files_to_process = []
    header_files_to_process = []
    for root, _, files in os.walk(src_path):
        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(src_path)
            output_dir = dst_path / relative_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)

            if file.endswith('.spec'):
                output_file = output_dir / (file_path.stem + '.c')
                spec_files_to_process.append((file_path, relative_path, output_file))
            elif file.endswith('.header'):
                output_file = output_dir / (file_path.stem + '.h')
                header_files_to_process.append((file_path, relative_path, output_file))
    
    return spec_files_to_process, header_files_to_process

def spec2code(root_dir: Path, logger: Logger, type: str, max_workers: int=10, dst_name: str=None):
    if type == "gen":
        src_path = root_dir / "specfs"
    elif type == "evolve":
        src_path = root_dir / "evolvefs"
    elif type == "virtio-blk":
        src_path = root_dir / "virtio-blk-spec"
    elif type == "evolve-virtio-blk":
        src_path = root_dir / "evolve-virtio-blk"
    elif type == "uart16550":
        src_path = root_dir / "uart16550-spec"
    elif type == "evolve-uart16550":
        src_path = root_dir / "evolve-uart16550"
    else:
        logger.error(f"Unknown type: {type}. Expected 'gen', 'evolve', 'virtio-blk', 'evolve-virtio-blk', 'uart16550', or 'evolve-uart16550'.")
        return

    dst_path = root_dir / (dst_name or "genfs")

    if not src_path.exists():
        logger.error("specfs directory not found!")
        return

    stats = {
        'total_spec_files': 0, 'total_header_files': 0,
        'spec_errors': 0, 'header_errors': 0
    }
    stats_lock = threading.Lock()

    spec_files_to_process, header_files_to_process = get_files_to_process(src_path, dst_path)

    total_to_process = len(spec_files_to_process) + len(header_files_to_process)
    if total_to_process == 0:
        logger.info("No files to update.")
        return
        
    tracker = ProgressTracker(total_to_process)

    for file_path, relative_path, output_file in header_files_to_process:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                header_content = f.read()
            
            h_content = generate_header_file(file_path.stem, header_content)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(h_content)
            
            tracker.update(str(relative_path))
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")
            stats['header_errors'] += 1

    spec_tasks_with_content = []
    for file_path, relative_path, output_file in spec_files_to_process:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                spec_content = f.read()

            orig_code = None
            orig_spec = None
            is_evolve = type in ("evolve", "evolve-virtio-blk", "evolve-uart16550")
            if is_evolve and output_file.exists():
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        orig_code = f.read()
                except Exception as e:
                    logger.error(f"Error reading existing output file {output_file}: {e}")

                # For evolve-virtio-blk, original spec is in virtio-blk-spec/
                if type == "evolve-virtio-blk":
                    spec_path = root_dir / "virtio-blk-spec"
                elif type == "evolve-uart16550":
                    spec_path = root_dir / "uart16550-spec"
                else:
                    spec_path = root_dir / "specfs"
                orig_spec_path = spec_path / relative_path
                if orig_spec_path.exists():
                    try:
                        with open(orig_spec_path, 'r', encoding='utf-8') as f:
                            orig_spec = f.read()
                    except Exception as e:
                        logger.error(f"Error reading original spec file {orig_spec_path}: {e}")
            
            spec_tasks_with_content.append((file_path, relative_path, output_file, spec_content, orig_code, orig_spec))
        except Exception as e:
            print(f"\nError reading {file_path}: {e}")
            stats['spec_errors'] += 1

    if spec_tasks_with_content:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            task_func = functools.partial(generate_c_file,
                                          stats_lock=stats_lock, 
                                          stats=stats, 
                                          logger=logger, 
                                          tracker=tracker)
            
            futures = [executor.submit(task_func, spec_info) for spec_info in spec_tasks_with_content]
            concurrent.futures.wait(futures)

    # ui_manager.finalize(stats) -> Simple summary print
    print("\n" + '━' * 60)
    print("✅ Code Generation Complete!")
    print(f"  - Spec: {stats['total_spec_files']} (Error: {stats['spec_errors']})")
    print(f"  - Header: {stats['total_header_files']} (Error: {stats['header_errors']})")
    sys.stdout.flush()
