import sys
from utils.logger import get_logger
logger = get_logger("startup_checks")

def run_checks():
    logger.info("Running Blend Engine startup checks...")
    success = True
    
    # Check Crawl4AI
    try:
        import crawl4ai
        logger.info("[OK] Crawl4AI is installed.")
    except ImportError:
        logger.warning("[WARNING] Crawl4AI is not installed. Deep Mode will have degraded functionality.")
        
    # Check Stem and Tor
    try:
        import stem
        from stem.control import Controller
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()
                logger.info("[OK] Tor daemon is running and accessible via stem on port 9051.")
        except Exception as e:
            logger.warning(f"[WARNING] Tor controller accessible, but authentication failed or daemon is unreachable: {e}")
            logger.warning("Ghost Mode and Deep Mode proxying will fail.")
            success = False
    except ImportError:
        logger.warning("[WARNING] Stem is not installed. Tor integration is disabled.")
        success = False
        
    # Check Bleach
    try:
        import bleach
        logger.info("[OK] Bleach is installed for HTML sanitization.")
    except ImportError:
        logger.warning("[WARNING] Bleach is not installed. Falling back to basic bs4 sanitization (less secure).")
        
    return success

if __name__ == "__main__":
    run_checks()
