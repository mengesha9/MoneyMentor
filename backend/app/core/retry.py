import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar, Optional

from app.core.constants import RETRY_CONFIG

logger = logging.getLogger(__name__)

T = TypeVar('T')

def async_retry(
    max_retries: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    exponential_base: Optional[float] = None
) -> Callable:
    """Decorator for retrying async functions with exponential backoff"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Use provided values or defaults from config
            max_retries_ = max_retries or RETRY_CONFIG["max_retries"]
            initial_delay_ = initial_delay or RETRY_CONFIG["initial_delay"]
            max_delay_ = max_delay or RETRY_CONFIG["max_delay"]
            exponential_base_ = exponential_base or RETRY_CONFIG["exponential_base"]
            
            last_exception = None
            
            for attempt in range(max_retries_):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries_ - 1:
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay_ * (exponential_base_ ** attempt),
                        max_delay_
                    )
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries_} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s. Error: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached due to the raise in the loop
            raise last_exception
            
        return wrapper
    return decorator 