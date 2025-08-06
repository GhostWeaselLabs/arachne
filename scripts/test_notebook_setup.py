#!/usr/bin/env python3
"""
Test script to validate Jupyter notebook setup for Meridian Runtime.
"""

import sys
import json
from pathlib import Path

def test_imports():
    """Test that all required libraries can be imported."""
    print("Testing imports...")
    
    try:
        import matplotlib.pyplot as plt
        print("✅ matplotlib imported successfully")
    except ImportError as e:
        print(f"❌ matplotlib import failed: {e}")
        return False
    
    try:
        import ipywidgets as widgets
        print("✅ ipywidgets imported successfully")
    except ImportError as e:
        print(f"❌ ipywidgets import failed: {e}")
        return False
    
    try:
        import plotly.graph_objects as go
        print("✅ plotly imported successfully")
    except ImportError as e:
        print(f"❌ plotly import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        import networkx as nx
        print("✅ networkx imported successfully")
    except ImportError as e:
        print(f"❌ networkx import failed: {e}")
        return False
    
    try:
        import seaborn as sns
        print("✅ seaborn imported successfully")
    except ImportError as e:
        print(f"❌ seaborn import failed: {e}")
        return False
    
    return True

def test_meridian_import():
    """Test that Meridian Runtime can be imported."""
    print("\nTesting Meridian Runtime import...")
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    try:
        from meridian.core import Node, Message, MessageType, Subgraph, Scheduler
        print("✅ Meridian Runtime core imported successfully")
    except ImportError as e:
        print(f"❌ Meridian Runtime core import failed: {e}")
        return False
    
    try:
        from meridian.observability.config import ObservabilityConfig, configure_observability
        print("✅ Meridian Runtime observability imported successfully")
    except ImportError as e:
        print(f"❌ Meridian Runtime observability import failed: {e}")
        return False
    
    return True

def test_notebook_structure():
    """Test that notebook directory structure exists."""
    print("\nTesting notebook structure...")
    
    notebooks_dir = Path("notebooks")
    if not notebooks_dir.exists():
        print("❌ notebooks/ directory not found")
        return False
    
    tutorials_dir = notebooks_dir / "tutorials"
    if not tutorials_dir.exists():
        print("❌ notebooks/tutorials/ directory not found")
        return False
    
    examples_dir = notebooks_dir / "examples"
    if not examples_dir.exists():
        print("❌ notebooks/examples/ directory not found")
        return False
    
    research_dir = notebooks_dir / "research"
    if not research_dir.exists():
        print("❌ notebooks/research/ directory not found")
        return False
    
    print("✅ Notebook directory structure exists")
    return True

def test_notebook_files():
    """Test that notebook files exist and are valid JSON."""
    print("\nTesting notebook files...")
    
    getting_started = Path("notebooks/tutorials/01-getting-started.ipynb")
    if not getting_started.exists():
        print("❌ 01-getting-started.ipynb not found")
        return False
    
    try:
        with open(getting_started, 'r') as f:
            notebook_data = json.load(f)
        
        # Validate notebook structure
        if 'cells' not in notebook_data:
            print("❌ Notebook missing 'cells' key")
            return False
        
        if 'metadata' not in notebook_data:
            print("❌ Notebook missing 'metadata' key")
            return False
        
        if 'nbformat' not in notebook_data:
            print("❌ Notebook missing 'nbformat' key")
            return False
        
        print(f"✅ 01-getting-started.ipynb is valid JSON with {len(notebook_data['cells'])} cells")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Notebook is not valid JSON: {e}")
        return False

def test_requirements():
    """Test that requirements.txt exists."""
    print("\nTesting requirements.txt...")
    
    requirements_file = Path("notebooks/requirements.txt")
    if not requirements_file.exists():
        print("❌ notebooks/requirements.txt not found")
        return False
    
    print("✅ requirements.txt exists")
    return True

def test_readme():
    """Test that README.md exists."""
    print("\nTesting README.md...")
    
    readme_file = Path("notebooks/README.md")
    if not readme_file.exists():
        print("❌ notebooks/README.md not found")
        return False
    
    print("✅ README.md exists")
    return True

def main():
    """Run all tests."""
    print("🧪 Testing Jupyter Notebook Setup for Meridian Runtime")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_meridian_import,
        test_notebook_structure,
        test_notebook_files,
        test_requirements,
        test_readme
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Notebook setup is ready.")
        print("\nNext steps:")
        print("1. Start Jupyter: uv run jupyter lab")
        print("2. Navigate to notebooks/tutorials/01-getting-started.ipynb")
        print("3. Run the cells to test the interactive features")
        return 0
    else:
        print("❌ Some tests failed. Please check the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
