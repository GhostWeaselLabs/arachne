#!/usr/bin/env python3
"""Subgraph generator CLI for Arachne.

Generates subgraph class skeletons with wiring stubs and tests.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .parsers.ports import snake_case
from .templates.subgraph import generate_subgraph_template, generate_subgraph_test_template


def create_directories(target_path: Path) -> None:
    """Create necessary directories for the target path."""
    target_path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str, force: bool = False) -> bool:
    """Write content to file, checking for existing files unless force=True."""
    if path.exists() and not force:
        print(f"Error: {path} already exists. Use --force to overwrite.")
        return False

    with open(path, "w") as f:
        f.write(content)
    print(f"Generated: {path}")
    return True


def create_subgraph_files(
    name: str,
    package: str,
    base_dir: str,
    include_tests: bool = False,
    force: bool = False,
) -> bool:
    """Generate subgraph files and optionally test files."""

    if not name.isidentifier() or not name[0].isupper():
        print("Error: Invalid class name. Use PascalCase without special characters.")
        return False
    # Create package directory structure
    package_parts = package.split(".")
    target_path = Path(base_dir)
    package_dir = target_path
    for part in package_parts:
        package_dir = package_dir / part

    create_directories(package_dir)

    # Generate __init__.py files for package structure
    current_dir = target_path
    for part in package_parts:
        current_dir = current_dir / part
        init_file = current_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Package initialization."""\n')

    # Generate subgraph file
    subgraph_filename = f"{snake_case(name)}.py"
    subgraph_path = package_dir / subgraph_filename
    subgraph_content = generate_subgraph_template(name)

    if not write_file(subgraph_path, subgraph_content, force):
        return False

    # Generate test file if requested
    if include_tests:
        test_dir = Path(base_dir).parent / "tests" / "integration"
        test_dir.mkdir(parents=True, exist_ok=True)

        test_filename = f"test_{snake_case(name)}.py"
        test_path = test_dir / test_filename
        test_content = generate_subgraph_test_template(name)

        if not write_file(test_path, test_content, force):
            return False

    return True


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate Arachne subgraph templates")
    parser.add_argument("--name", required=True, help="Subgraph class name (PascalCase)")
    parser.add_argument("--package", default="subgraphs", help="Package path (dot-separated)")
    parser.add_argument("--dir", default="src/meridian-runtime", help="Target directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--include-tests", action="store_true", help="Generate test files")

    args = parser.parse_args()

    # Generate files
    Path(args.dir).mkdir(parents=True, exist_ok=True)
    success = create_subgraph_files(
        name=args.name,
        package=args.package,
        base_dir=args.dir,
        include_tests=args.include_tests,
        force=args.force,
    )

    if not success:
        sys.exit(1)

    created_path = Path(args.dir) / args.package.replace(".", "/") / (snake_case(args.name) + ".py")
    print(f"Created subgraph: {created_path}")
    if args.include_tests:
        test_created = (
            Path(args.dir).parent
            / "tests"
            / "integration"
            / ("test_" + snake_case(args.name) + ".py")
        )
        print(f"Created test: {test_created}")
    print(f"Successfully generated {args.name} subgraph in {args.package}")


if __name__ == "__main__":
    main()
