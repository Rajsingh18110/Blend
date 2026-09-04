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

def main():
    parser = argparse.ArgumentParser(description="Blend Search CLI")
    parser.add_argument('command', nargs='?', choices=['stop'], help="Stop the background server")
    parser.add_argument('--no-browser', action='store_true', help="Don't open browser")
    parser.add_argument('--daemon-worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()

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
    
if __name__ == '__main__':
    main()
