#!/usr/bin/env python3
"""
Utility script to clear the bus routing cache.
Run this if you update the CSV/JSON data files and want to force a rebuild.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import graph_cache
    graph_cache.clear_cache()
    print("\n✅ Cache cleared successfully!")
    print("💡 Next server start will rebuild the graph from scratch.")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
