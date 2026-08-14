'''
Sift test suite: generate a directory of test files
'''

# -- Import external dependencies --
import subprocess
from pathlib import Path
from typing import Optional


# -- _ask_for_input: asks user for input via terminal, using Rich where available and defaulting to standard input --
def _ask_for_input(prompt: str, options: Optional[list] = None, default: Optional[str | bool] = None, confirm: bool = False):
    # Try with Rich first
    try:
        default = default if default else None
        if confirm:
            from rich.prompt import Confirm
            return Confirm.ask(prompt=f'{prompt}? ', choices=options, default=default)
        else:
            from rich.prompt import Prompt
            return Prompt.ask(prompt=f'{prompt}: ', choices=options, default=default)
    except ModuleNotFoundError:
        if confirm:
            # Convert default value to bool if required
            if type(default) is str:
                default = True if default.strip().lower() == 'y' else False
            prompt = f'{prompt} (Y/n)? ' if default else f'{prompt} (y/N)? '
            while True:
                val = input(prompt).strip().lower()
                if val == '':
                    return default
                elif val == 'y':
                    return True
                elif val == 'n':
                    return False
        else:
            prompt = f'{prompt} {options}' if options else f'{prompt}'
            prompt = f'{prompt}:'.replace(f"'{default}'", "'"+default+"' (default)") if default else f'{prompt}: '
            while True:
                val = input(prompt).strip().lower()
                if val == '' and default:
                    return default
                if options:
                    if val in [o.strip().lower() for o in options]:
                        return val
                elif not options:   
                    return val

# -- generate_test_files: generates a directory of test files --
def generate_test_files(path: Path = Path('.')):
    out_dir = path / 'test_files'
    # Create overall directory
    out_dir.mkdir(parents=True, exist_ok=True)
    # Create subdirectories
    sub_dirs = ['src', 'dest1', 'dest2']
    for s in sub_dirs:
        Path(out_dir, s).mkdir(parents=True, exist_ok=True)
    files = ['example_txt.txt', 'example_md.md', 'example_pdf.pdf', 'example_mp4.mp4']
    for f in files:
        Path(out_dir, 'src', f).touch()    
    return out_dir, out_dir.iterdir()


# -- run_ui_test: generates a directory of test files, runs Sift to test UI, and cleans up test files --
def run_ui_test(path: Path | None = None):
    # Generate files
    file_dir, file_paths = generate_test_files(path)
    # Run Sift
    subprocess.run(args=['sift'])
    # Confirm whether to clean up test files
    clean_files = _ask_for_input(prompt='Delete generated test files', default=True, confirm=True)
    if clean_files:
        # Delete files
        import shutil
        shutil.rmtree(file_dir)
        for f in file_paths:
            if f.exists():
                print(f'Error deleting file: {f}')
    return

if __name__ == '__main__':
    print()
    mode = _ask_for_input(prompt='Run mode', options=['generate files', 'test UI'], default = 'test UI')
    target_dir = Path(_ask_for_input(prompt='Directory to generate files within', default = '.'))
    print()
    if mode == 'generate_files':
        file_dir, file_paths = generate_test_files(target_dir)
        print(f'\nGenerated files in {file_dir}: {', '.join(file_paths)}')
    elif mode == 'test UI':
        run_ui_test(target_dir)
    