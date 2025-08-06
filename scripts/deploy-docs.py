#!/usr/bin/env python3
"""
Script to deploy built documentation to the meridian-runtime-docs repository.
This script uses the GitHub API to push the built site files.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def main():
    # Get the GitHub token from environment
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Paths
    site_dir = Path("site")
    target_repo = "ghostweasellabs/meridian-runtime-docs"
    
    if not site_dir.exists():
        print("Error: site directory not found. Run 'uv run mkdocs build' first.")
        sys.exit(1)
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Clone the target repository
        clone_url = f"https://x-access-token:{token}@github.com/{target_repo}.git"
        if not run_command(f"git clone {clone_url} target-repo", cwd=temp_path):
            sys.exit(1)
        
        target_path = temp_path / "target-repo"
        
        # Remove all existing content
        for item in target_path.iterdir():
            if item.name != ".git":
                if item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)
        
        # Copy the built site
        for item in site_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, target_path)
            else:
                shutil.copytree(item, target_path / item.name)
        
        # Configure git
        run_command("git config user.name 'github-actions[bot]'", cwd=target_path)
        run_command("git config user.email 'github-actions[bot]@users.noreply.github.com'", cwd=target_path)
        
        # Add and commit
        if not run_command("git add -A", cwd=target_path):
            sys.exit(1)
        
        commit_msg = f"Deploy docs from meridian-runtime@$(git rev-parse HEAD)"
        if not run_command(f'git commit -m "{commit_msg}"', cwd=target_path):
            sys.exit(1)
        
        # Push
        if not run_command("git push origin main", cwd=target_path):
            sys.exit(1)
    
    print("Deployment completed successfully!")

if __name__ == "__main__":
    main()
