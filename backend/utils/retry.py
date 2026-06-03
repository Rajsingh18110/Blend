import asyncio
from typing import Callable, Any
from .logger import get_logger

logger = get_logger("retry_logic")

async def async_retry(func: Callable, retries: int = 3, base_delay: float = 1.0, *args, **kwargs) -> Any:
    """Executes an async function with exponential backoff retry logic."""
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == retries - 1:
                logger.error(f"Task failed after {retries} attempts: {e}")
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
