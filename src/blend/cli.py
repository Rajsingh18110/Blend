import argparse
import os
import socket
import webbrowser
import sys
import signal
import subprocess
from platformdirs import user_data_dir

BANNER = r"""
  ____  _              _
 | __ )| | ___ _ __   __| |
 |  _ \| |/ _ \ '_ \ / _` |
 | |_) | |  __/ | | | (_| |
 |____/|_|\___|_| |_|\__,_|

 Blend — made by MarkanM
"""

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_if_running():
    data_dir = user_data_dir("blend", "markanm")
    pid_file = os.path.join(data_dir, "blend.pid")
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            try:
                pid = int(f.read().strip())
                os.kill(pid, 0)
                return True
            except:
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

def update_binary():
    import urllib.request
    import platform
    print("Fetching latest release information...")
    # Assuming GitHub releases are uploaded with these names
    base_url = "https://github.com/Rajsingh18110/Blend/releases/latest/download"
    os_name = platform.system().lower()
    if os_name == "windows":
        file_name = "blend-windows.zip"
    elif os_name == "darwin":
        file_name = "blend-macos.tar.gz"
    else:
        file_name = "blend-linux.tar.gz"
    
    download_url = f"{base_url}/{file_name}"
    print(f"Downloading {file_name} from {download_url} ...")
    try:
        urllib.request.urlretrieve(download_url, file_name)
        print(f"✅ Update downloaded successfully as {file_name}!")
        print("Please extract and replace your current executable.")
    except Exception as e:
        print(f"❌ Failed to download update: {e}")
        print("Make sure a release exists on GitHub.")

def update_code():
    import subprocess
    print("Pulling latest source code from GitHub...")
    try:
        # Check if we are in a git repository
        if os.path.exists(".git"):
            subprocess.check_call(["git", "pull"])
            print("✅ Source code updated successfully using git pull!")
        else:
            # If not a git repo, upgrade via pip from main branch
            print("Not a git repository. Upgrading via pip...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "git+https://github.com/Rajsingh18110/Blend.git"])
            print("✅ Package updated successfully from GitHub main branch!")
    except Exception as e:
        print(f"❌ Failed to update code: {e}")

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

    if args.daemon_worker:
        with open(get_pid_file(), 'w') as f:
            f.write(str(os.getpid()))
        os.environ['BLEND_EMBEDDED_BACKEND'] = '1'
        from blend.app import app
        import logging
        logging.getLogger('werkzeug').disabled = True
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        sys.exit(0)

    if check_if_running():
        print("Blend server is already running in the background.")
        if not args.no_browser:
            webbrowser.open("http://127.0.0.1:5000")
        sys.exit(0)

    print(BANNER)
    print("  Local:        http://127.0.0.1:5000")
    print("  Admin panel:  http://127.0.0.1:5000/admin")
    print("\n  🚀 Running in background! (Type 'blend stop' to shut down)")

    if not args.no_browser:
        webbrowser.open("http://127.0.0.1:5000")

    pid_file = get_pid_file()
    if os.path.exists(pid_file):
        os.remove(pid_file)

    log_path = os.path.join(user_data_dir("blend", "markanm"), "server_log.txt")
    with open(log_path, 'a') as f:
        proc = subprocess.Popen([sys.executable, "-m", "blend.cli", "--daemon-worker"],
                         stdout=f, stderr=subprocess.STDOUT, start_new_session=True)

def code_updater():
    if '-update' in sys.argv or '--update' in sys.argv:
        update_code()
    else:
        print("Usage: blendcode -update")
        sys.exit(1)

if __name__ == '__main__':
    main()

