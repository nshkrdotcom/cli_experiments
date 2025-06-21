#!/usr/bin/env python3
"""
Self-Evolving CLI Tool Entry Point
A foundation for AGI platform development with self-modification capabilities.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from cli import main

if __name__ == "__main__":
    main()
