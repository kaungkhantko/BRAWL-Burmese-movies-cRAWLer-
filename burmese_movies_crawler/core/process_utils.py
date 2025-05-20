"""
Process utilities for the Burmese Movies Crawler.

This module provides functions for handling processes, timeouts, and subprocess execution.
"""

import subprocess
import time
from threading import Timer
from typing import Optional, Callable, List


def timeout_handler(process: subprocess.Popen) -> None:
    """
    Kill the process when timeout is reached.
    
    Args:
        process: The process to kill
    """
    if process.poll() is None:  # If process is still running
        print("Timeout reached. Terminating crawler...")
        process.terminate()
        # Give it a moment to terminate gracefully
        time.sleep(2)
        # Force kill if still running
        if process.poll() is None:
            process.kill()


def run_with_timeout(
    command: List[str], 
    timeout_seconds: int = 90, 
    on_start: Optional[Callable] = None,
    on_finish: Optional[Callable] = None
) -> subprocess.Popen:
    """
    Run a command with a timeout.
    
    Args:
        command: The command to run
        timeout_seconds: The timeout in seconds
        on_start: Optional callback to run when the process starts
        on_finish: Optional callback to run when the process finishes
        
    Returns:
        The process object
    """
    print(f"Running command with {timeout_seconds} second timeout...")
    
    # Use Popen to be able to set a timeout
    process = subprocess.Popen(command)
    
    if on_start:
        on_start(process)
    
    # Set a timer to kill the process after the timeout
    timer = Timer(timeout_seconds, timeout_handler, [process])
    
    try:
        timer.start()
        process.wait()
    finally:
        timer.cancel()  # Cancel the timer if process finishes before timeout
        
    if on_finish:
        on_finish(process)
        
    return process