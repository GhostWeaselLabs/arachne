#!/usr/bin/env python3
"""Node generator CLI for Arachne.

Generates node class skeletons with proper typing, lifecycle hooks, and tests.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .parsers.ports import (
    parse_ports,
    snake_case,  # re-export for tests
)
from .templates.node import (
    generate_node_template,
    generate_node_test_template,
)

# Temporary legacy wrapper for backward compatibility; deprecate before 1.0


def generate_test_template(name: str, module: str) -> str:  # pragma: no cover
    from .templates.node import generate_test_template as _gen

    return _gen(name, module)


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


def create_node_files(
    name: str,
    package: str,
    inputs: dict[str, str],
    outputs: dict[str, str],
    base_dir: str,
    include_tests: bool = False,
    force: bool = False,
    policy: str | None = None,
) -> bool:
    """Generate node files and optionally test files."""

    if not name.isidentifier() or not name[0].isupper():
        print("Error: Invalid class name. Use PascalCase without special characters.")
        return False
    # Create package directory structure
    package_parts = package.split(".")
    package_dir = Path(base_dir)
    for part in package_parts:
        package_dir = package_dir / part

    create_directories(package_dir)

    # Generate __init__.py files for package structure
    current_dir = Path(base_dir)
    for part in package_parts:
        current_dir = current_dir / part
        init_file = current_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Package initialization."""\n')

    # Generate node file
    node_filename = f"{snake_case(name)}.py"
    node_path = package_dir / node_filename
    node_content = generate_node_template(name, inputs, outputs, policy)

    if not write_file(node_path, node_content, force):
        return False

    # Generate test file if requested
    if include_tests:
        test_dir = Path(base_dir).parent / "tests" / "unit"
        test_dir.mkdir(parents=True, exist_ok=True)

        test_filename = f"test_{snake_case(name)}.py"
        test_path = test_dir / test_filename
        test_content = generate_node_test_template(name, inputs, outputs)

        if not write_file(test_path, test_content, force):
            return False

    return True


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate Arachne node templates")
    parser.add_argument("--name", required=True, help="Node class name (PascalCase)")
    parser.add_argument("--package", default="nodes", help="Package path (dot-separated)")
    parser.add_argument("--inputs", default="", help="Input ports (name:type,name:type)")
    parser.add_argument("--outputs", default="", help="Output ports (name:type,name:type)")
    parser.add_argument("--dir", default="src/meridian-runtime", help="Target directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--include-tests", action="store_true", help="Generate test files")
    parser.add_argument("--policy", default=None, help="Default overflow policy")

    args = parser.parse_args()

    # Parse ports
    try:
        inputs = parse_ports(args.inputs)
        outputs = parse_ports(args.outputs)
    except Exception as e:
        print(f"Error parsing ports: {e}")
        sys.exit(1)

    # Generate files
    Path(args.dir)
    success = create_node_files(
        name=args.name,
        package=args.package,
        inputs=inputs,
        outputs=outputs,
        base_dir=args.dir,
        include_tests=args.include_tests,
        force=args.force,
        policy=args.policy,
    )

    if not success:
        sys.exit(1)

    node_path = Path(args.dir) / args.package.replace(".", "/") / f"{snake_case(args.name)}.py"
    print(f"Created node: {node_path}")
    if args.include_tests:
        test_path = Path(args.dir).parent / "tests" / "unit" / f"test_{snake_case(args.name)}.py"
        print(f"Created test: {test_path}")
    print(f"Successfully generated {args.name} node in {args.package}")


if __name__ == "__main__":
    main()
