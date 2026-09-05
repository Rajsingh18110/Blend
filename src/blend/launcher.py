import sys
import os
import platform
import urllib.request
import subprocess
import stat

def get_binary_path():
    os_name = platform.system().lower()
    
    if os_name == "windows":
        data_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Blend")
        bin_name = "blend-bin.exe"
    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".local", "bin")
        bin_name = "blend-bin"
        
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, bin_name)

def report_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = downloaded * 100 / total_size
        sys.stdout.write(f"\r📥 Downloading Blend: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
        sys.stdout.flush()
    else:
        sys.stdout.write(f"\r📥 Downloading Blend: {downloaded / (1024*1024):.1f} MB downloaded...")
        sys.stdout.flush()

def download_binary(binary_path):
    os_name = platform.system().lower()
    base_url = "https://github.com/Rajsingh18110/Blend/releases/latest/download"
    
    if os_name == "windows":
        url = f"{base_url}/blend.exe"
    elif os_name == "darwin":
        url = f"{base_url}/blend-macos"
    else:
        url = f"{base_url}/blend-linux"
        
    print(f"Fetching updates for {os_name} from GitHub...")
    
    try:
        urllib.request.urlretrieve(url, binary_path, reporthook=report_progress)
        print("\n✅ Download successful!")
        
        # Set executable permissions on Linux/macOS
        if os_name != "windows":
            st = os.stat(binary_path)
            os.chmod(binary_path, st.st_mode | stat.S_IEXEC)
            
    except Exception as e:
        print(f"\n❌ Failed to download Blend. Error: {e}")
        sys.exit(1)

def main():
    binary_path = get_binary_path()
    
    # Check if user explicitly asked for an update
    if "-update" in sys.argv or "--update" in sys.argv:
        download_binary(binary_path)
        sys.exit(0)
        
    if not os.path.exists(binary_path):
        print("Blend executable not found locally. Initializing...")
        download_binary(binary_path)
        
    # Execute the downloaded binary
    try:
        if platform.system().lower() != "windows":
            # On POSIX systems, replace the current process (more native feel)
            os.execv(binary_path, [binary_path] + sys.argv[1:])
        else:
            # On Windows, os.execv doesn't work perfectly with child lifecycles
            sys.exit(subprocess.call([binary_path] + sys.argv[1:]))
    except Exception as e:
        print(f"❌ Failed to execute Blend binary: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
