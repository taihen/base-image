#!/usr/bin/env python3
import socket
import platform
import sys

def main():
    hostname = socket.gethostname()
    print(f"Hello from {hostname}!")
    
    # Get OS and architecture info
    system = platform.system()
    machine = platform.machine()
    print(f"Running on {system}/{machine}")
    
    # Get Python version
    python_version = sys.version.split()[0]
    print(f"Built with Python {python_version}")

if __name__ == "__main__":
    main() 