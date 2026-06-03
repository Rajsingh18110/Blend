import threading
import time
try:
    from stem import Signal
    from stem.control import Controller
except ImportError:
    pass

class TorManager:
    """
    Manages Tor circuits and identity rotation for absolute privacy.
    Requires tor and stem to be installed and running on port 9051.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TorManager, cls).__new__(cls)
                cls._instance.last_rotation = 0
                cls._instance.rotation_interval = 30 # seconds minimum between rotations
        return cls._instance

    def rotate_identity(self) -> bool:
        """
        Request a new Tor circuit (NEWNYM) to change exit node IP.
        """
        current_time = time.time()
        if current_time - self.last_rotation < self.rotation_interval:
            return False # Too soon to rotate
            
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate() # Ensure torrc has CookieAuthentication 1 or no password
                controller.signal(Signal.NEWNYM)
                self.last_rotation = current_time
                return True
        except Exception as e:
            print(f"Tor rotation failed: {e}")
            return False

    def get_proxy_url(self) -> str:
        """Return the socks5 proxy URL for aiohttp/requests."""
        return "socks5://127.0.0.1:9050"
