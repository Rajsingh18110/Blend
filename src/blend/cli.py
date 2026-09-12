import argparse
import itertools
import json
import os
import shutil
import socket
import threading
import time
import webbrowser
import sys
import signal
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from platformdirs import user_data_dir

BANNER = r"""
  ____  _              _
 | __ )| | ___ _ __   __| |
 |  _ \| |/ _ \ '_ \ / _` |
 | |_) | |  __/ | | | (_| |
 |____/|_|\___|_| |_|\__,_|

 Blend — made by MarkanM
"""

def get_blend_version():
    try:
        import blend as blend_pkg
        return getattr(blend_pkg, "__version__", "unknown")
    except Exception:
        return "unknown"


def get_backend_port():
    return int(os.environ.get("BLEND_PORT", "5000"))


def find_available_port(start_port=5000, max_attempts=50):
    """Return the first free localhost port starting from start_port."""
    port = int(start_port)
    for offset in range(max_attempts):
        candidate = port + offset
        if candidate > 65535:
            break
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(('127.0.0.1', candidate))
                return candidate
            except OSError:
                continue
    raise RuntimeError(f"No free localhost port found from {start_port} to {start_port + max_attempts - 1}.")


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def check_if_running(port=None):
    port = port or get_backend_port()
    if is_port_in_use(port):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/ping", timeout=1) as response:
                payload = json.loads(response.read().decode('utf-8'))
            if payload.get("server") == "blend_server" or payload.get("status") == "ok":
                return True
        except Exception:
            pass

    data_dir = user_data_dir("blend", "markanm")
    pid_file = os.path.join(data_dir, "blend.pid")
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            try:
                pid = int(f.read().strip())
                os.kill(pid, 0)
                return True
            except Exception:
                pass
    return False

def get_pid_file():
    data_dir = user_data_dir("blend", "markanm")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "blend.pid")

def kill_running():
    pid_file = get_pid_file()
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            try:
                pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                print(f"🛑 Stopped Blend server (PID {pid}).")
            except Exception:
                pass
        os.remove(pid_file)

def update_blend():
    import subprocess
    import sys
    import os
    print("Fetching the latest Blend code from GitHub...")
    try:
        if os.path.exists(".git"):
            subprocess.check_call(["git", "pull"])
            print("✅ Source code updated successfully using git pull!")
        else:
            print("Downloading and installing latest version...")
            zip_url = "https://github.com/Rajsingh18110/Blend/archive/refs/heads/main.zip"
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", zip_url])
            print("✅ Blend updated successfully from GitHub!")
    except Exception as e:
        print(f"❌ Failed to update Blend: {e}")

def update_binary():
    update_blend()

def update_code():
    update_blend()

def main():
    parser = argparse.ArgumentParser(description="Blend Search CLI")
    parser.add_argument('command', nargs='?', choices=['stop'], help="Stop the background server")
    parser.add_argument('--no-browser', action='store_true', help="Don't open browser")
    parser.add_argument('-update', '--update', action='store_true', help="Download the latest binary update")
    parser.add_argument('--daemon-worker', action='store_true', help=argparse.SUPPRESS)
    args, unknown = parser.parse_known_args()

    if getattr(args, 'update', False) or '-update' in sys.argv:
        update_binary()
        sys.exit(0)

    if args.command == 'stop':
        kill_running()
        sys.exit(0)

    port = get_backend_port()
    if is_port_in_use(port) and not check_if_running(port):
        next_port = find_available_port(start_port=port + 1)
        print(f"⚠️ Port {port} is already in use by another process. Using port {next_port} for Blend instead.")
        port = next_port
        os.environ['BLEND_PORT'] = str(port)

    if args.daemon_worker:
        with open(get_pid_file(), 'w') as f:
            f.write(str(os.getpid()))
        os.environ['BLEND_EMBEDDED_BACKEND'] = '1'
        os.environ['BLEND_PORT'] = str(port)
        from blend.app import app
        import logging
        logging.getLogger('werkzeug').disabled = True
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
        sys.exit(0)

    if check_if_running(port):
        print(f"Blend server is already running in the background on http://127.0.0.1:{port}.")
        if not args.no_browser:
            webbrowser.open(f"http://127.0.0.1:{port}")
        sys.exit(0)

    print(BANNER)
    print(f"  Local:        http://127.0.0.1:{port}")
    print(f"  Admin panel:  http://127.0.0.1:{port}/admin")
    print("\n  🚀 Running in background! (Type 'blend stop' to shut down)")

    pid_file = get_pid_file()
    if os.path.exists(pid_file):
        os.remove(pid_file)

    log_path = os.path.join(user_data_dir("blend", "markanm"), "server_log.txt")
    with open(log_path, 'a') as f:
        kwargs = {}
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs['start_new_session'] = True
        
        # Ensure the spawned subprocess inherits the local `src` package path
        # so `import blend` resolves to the working tree when running from
        # source. Also set a sensible working directory (repo root) so relative
        # template/resource paths resolve in the child.
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        src_dir = os.path.join(repo_root, 'src')
        env = os.environ.copy()
        env['BLEND_PORT'] = str(port)
        prev_pp = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = src_dir + (os.pathsep + prev_pp if prev_pp else '')

        if getattr(sys, 'frozen', False):
            meipass = getattr(sys, '_MEIPASS', None)
            blend_version = get_blend_version()
            persistent_meipass = os.path.join(user_data_dir("blend", "markanm"), f"meipass_cache_{blend_version}")
            
            if meipass and not os.path.exists(persistent_meipass):
                import shutil
                shutil.copytree(meipass, persistent_meipass)
                
            cmd = [sys.executable, "--daemon-worker"]
            # ensure the frozen child also gets the persistent meipass and
            # a PYTHONPATH that includes the extracted directory (best-effort)
            env['_MEIPASS2'] = persistent_meipass
            env['_MEIPASS'] = persistent_meipass
            env['_PYI_APPLICATION_HOME_DIR'] = persistent_meipass
            if 'LD_LIBRARY_PATH' in env and meipass:
                env['LD_LIBRARY_PATH'] = env['LD_LIBRARY_PATH'].replace(meipass, persistent_meipass)
            # point PYTHONPATH to the persistent meipass so packages in the
            # extracted bundle can be imported if needed
            env['PYTHONPATH'] = persistent_meipass + (':' + env.get('PYTHONPATH', '') if env.get('PYTHONPATH') else '')
            kwargs['env'] = env
        else:
            cmd = [sys.executable, "-m", "blend.cli", "--daemon-worker"]
            # pass our prepared env so the child resolves the local `src` tree
            kwargs['env'] = env
            # ensure the child runs with the repo root as cwd so relative file
            # accesses (templates/static) work as expected
            kwargs['cwd'] = repo_root
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, **kwargs)

    if not args.no_browser:
        import time
        time.sleep(1.5)  # Give the server a moment to start
        target_url = f"http://127.0.0.1:{port}"
        try:
            webbrowser.open(target_url)
        except Exception:
            print("Could not open the browser automatically.")
            print(f"Please click or copy-paste this link: {target_url}")

def parse_code_install_args(argv=None):
    parser = argparse.ArgumentParser(description="Download and install the Blend source code from GitHub.")
    parser.add_argument('mode', nargs='?', choices=['all', 'clone', 'install', 'download'], help="Code install mode")
    parser.add_argument('-all', '--all', dest='all', action='store_true', help="Download the full source code and install requirements")
    parser.add_argument('--target-dir', default=str(Path.cwd() / 'Blend'), help="Target folder for the source checkout")
    parser.add_argument('--skip-requirements', action='store_true', help="Skip installing requirements.txt")
    parser.add_argument('--no-animation', action='store_true', help="Disable the animated installer output")
    args = parser.parse_args(argv)
    if args.mode is None and not args.all:
        args.all = True
    elif args.mode == 'all' or args.all:
        args.all = True
    return args


def run_with_spinner(command, message, cwd=None, env=None):
    if env is None:
        env = os.environ.copy()

    if cwd is not None:
        cwd = str(cwd)

    proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    stop_event = threading.Event()

    def animate():
        while not stop_event.is_set():
            sys.stdout.write(f"\r{next(spinner)} {message}")
            sys.stdout.flush()
            time.sleep(0.08)
        sys.stdout.write(f"\r✓ {message}\n")
        sys.stdout.flush()

    thread = threading.Thread(target=animate, daemon=True)
    thread.start()
    try:
        output, _ = proc.communicate()
    finally:
        stop_event.set()
        thread.join()

    if output:
        print(output.rstrip())
    return proc.returncode


def install_source_tree(target_dir=None, include_requirements=True, show_animation=True):
    repo_url = "https://github.com/Rajsingh18110/Blend.git"
    target_dir = Path(target_dir or Path.cwd() / 'Blend').expanduser().resolve()
    repo_root = target_dir

    print(f"\n📦 Preparing Blend source install in {target_dir}\n")

    if target_dir.exists() and (target_dir / '.git').exists():
        print("🔄 Repository already exists; pulling latest code...")
        git_cmd = ['git', '-C', str(target_dir), 'pull', '--ff-only']
        git_rc = run_with_spinner(git_cmd, 'Updating source code...') if show_animation else subprocess.run(git_cmd, capture_output=True, text=True).returncode
        if git_rc != 0:
            print("⚠️ Git pull failed. Re-cloning the repository...")
            shutil.rmtree(target_dir, ignore_errors=True)
            return install_source_tree(target_dir=target_dir, include_requirements=include_requirements, show_animation=show_animation)
        repo_root = target_dir
    else:
        if target_dir.exists() and not target_dir.is_dir():
            raise ValueError(f"Target path is not a directory: {target_dir}")

        if target_dir.exists() and any(target_dir.iterdir()):
            print(f"⚠️ Directory exists and is not an empty git checkout: {target_dir}")
            print("Using the existing folder as the project root.")
            repo_root = target_dir
        else:
            print("⬇️ Cloning the repository from GitHub...")
            clone_cmd = ['git', 'clone', '--depth', '1', repo_url, str(target_dir)]
            if show_animation:
                clone_rc = run_with_spinner(clone_cmd, 'Cloning repository from GitHub...')
            else:
                clone_rc = subprocess.run(clone_cmd, capture_output=True, text=True).returncode
            if clone_rc != 0:
                print("⚠️ Git clone failed. Falling back to the GitHub ZIP download...")
                zip_url = "https://github.com/Rajsingh18110/Blend/archive/refs/heads/main.zip"
                zip_path = target_dir.parent / 'Blend-main.zip'
                try:
                    if zip_path.exists():
                        zip_path.unlink()
                    urllib.request.urlretrieve(zip_url, zip_path)
                    with zipfile.ZipFile(zip_path) as zf:
                        zf.extractall(str(target_dir.parent))
                    extracted_dir = target_dir.parent / 'Blend-main'
                    if extracted_dir.exists() and target_dir.exists() is False:
                        extracted_dir.rename(target_dir)
                except Exception as exc:
                    print(f"❌ Source download failed: {exc}")
                    print("Manual fallback: download the ZIP from GitHub and extract it into a local folder.")
                    return 1
                repo_root = target_dir

    if include_requirements:
        req_path = repo_root / 'requirements.txt'
        if not req_path.exists():
            print(f"⚠️ requirements.txt not found in {repo_root}.")
            print("Skipping dependency installation because the repo layout does not include the file.")
            return 0

        print("📦 Installing Python dependencies from requirements.txt...")
        pip_cmd = [sys.executable, '-m', 'pip', 'install', '-r', str(req_path)]
        pip_rc = run_with_spinner(pip_cmd, 'Installing project requirements...', cwd=str(repo_root)) if show_animation else subprocess.run(pip_cmd, cwd=str(repo_root), capture_output=True, text=True).returncode

        if pip_rc != 0:
            print("⚠️ Dependency installation failed.")
            print("Manual fallback commands:")
            print(f"  cd \"{repo_root}\"")
            print("  python -m venv .venv")
            print("  . .venv/bin/activate")
            print("  python -m pip install --upgrade pip")
            print("  python -m pip install -r requirements.txt")
            print("  python -m blend.cli")
            return 1

    print("\n✅ Blend source is ready.")
    print(f"Run it with: cd \"{repo_root}\" && python -m blend.cli")
    return 0


def code_main(argv=None):
    args = parse_code_install_args(argv)
    if args.mode in {'all', 'clone', 'install', 'download'} or args.all or args.mode is None:
        return install_source_tree(target_dir=args.target_dir, include_requirements=not args.skip_requirements, show_animation=not args.no_animation)

    print("Usage: blendcode [all|clone|install|download] [--all] [--target-dir PATH]")
    print("Examples:")
    print("  blendcode")
    print("  blendcode --all")
    print("  blendcode all")
    print("  blendcode -all")
    print("  blendcode --target-dir ~/Blend")
    return 0


def code_updater():
    if '-update' in sys.argv or '--update' in sys.argv:
        update_code()
    else:
        print("Usage: blendcode -update")
        sys.exit(1)

if __name__ == '__main__':
    main()

