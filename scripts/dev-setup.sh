#!/usr/bin/env bash
#
# dev-setup.sh
#
# Bootstraps a local dev environment for Meridian Runtime contributors.
# - Installs pre-commit (if missing)
# - Installs lychee (internal docs link checker) via cargo, if available; optionally installs cargo if missing
# - Installs pre-commit hooks (commit + pre-push)
#
# Usage:
#   ./scripts/dev-setup.sh
#   # or make executable first:
#   chmod +x ./scripts/dev-setup.sh && ./scripts/dev-setup.sh
#
# Notes:
# - On macOS, Homebrew is used to install cargo if it's not found.
# - On Linux, attempts to install Rust toolchain via rustup (requires curl).
# - If lychee cannot be installed, you can still run pre-commit by skipping that hook:
#     SKIP=docs-lychee-internal pre-commit run --all-files

set -euo pipefail

say() { printf "\033[1;36m[dev-setup]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[dev-setup][warn]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[dev-setup][error]\033[0m %s\n" "$*"; }

have_cmd() { command -v "$1" >/dev/null 2>&1; }

install_pre_commit() {
  if have_cmd pre-commit; then
    say "pre-commit already installed: $(pre-commit --version)"
    return
  fi

  if have_cmd uv; then
    say "Installing pre-commit via 'uv tool install pre-commit'..."
    if uv tool install pre-commit; then
      say "pre-commit installed via uv tool."
      say "pre-commit version: $(pre-commit --version || true)"
      return
    else
      warn "'uv tool install pre-commit' failed; attempting uv-run pip fallback..."
      # Some environments lack pip in uv; we still try and fall back further if needed.
      if uv run pip install --upgrade pre-commit; then
        say "pre-commit installed via uv run pip"
        say "pre-commit version: $(pre-commit --version || true)"
        return
      fi
    fi
  fi

  say "Trying to install pre-commit via Python/pip (fallback path)..."
  if have_cmd python; then
    python -m pip install --upgrade pip || true
    if python -m pip install --upgrade pre-commit; then
      say "pre-commit installed via python -m pip"
      say "pre-commit version: $(pre-commit --version || true)"
      return
    fi
  fi

  if have_cmd pip; then
    if pip install --upgrade pre-commit; then
      say "pre-commit installed via pip"
      say "pre-commit version: $(pre-commit --version || true)"
      return
    fi
  fi

  err "Failed to install pre-commit. Please install manually:
    - Using uv:   uv tool install pre-commit
    - Using pip:  python -m pip install --upgrade pre-commit
  "
  return 1
}

install_rust_toolchain_if_needed() {
  if have_cmd cargo; then
    say "cargo already installed: $(cargo --version)"
    return
  fi

  say "cargo not found. Attempting to install Rust toolchain."
  uname_s="$(uname -s || echo unknown)"

  case "$uname_s" in
    Darwin)
      if have_cmd brew; then
        say "Installing Rust via Homebrew..."
        brew install rust || {
          err "Failed to install rust via brew. Please install rust (cargo) manually: https://www.rust-lang.org/tools/install"
          return 1
        }
      else
        warn "Homebrew not found. Please install Homebrew (https://brew.sh) or install Rust manually."
        warn "Attempting rustup install via curl..."
        if have_cmd curl; then
          curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y || {
            err "rustup installation failed. Install Rust manually: https://www.rust-lang.org/tools/install"
            return 1
          }
          # shellcheck disable=SC1090
          source "$HOME/.cargo/env" || true
        else
          err "curl not available to bootstrap rustup. Install Rust manually: https://www.rust-lang.org/tools/install"
          return 1
        fi
      fi
      ;;
    Linux)
      if have_cmd curl; then
        say "Installing Rust via rustup (Linux)..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y || {
          err "rustup installation failed. Install Rust manually: https://www.rust-lang.org/tools/install"
          return 1
        }
        # shellcheck disable=SC1090
        source "$HOME/.cargo/env" || true
      else
        err "curl not available to bootstrap rustup. Install Rust manually: https://www.rust-lang.org/tools/install"
        return 1
      fi
      ;;
    *)
      warn "Unsupported platform ($uname_s) for automated cargo install."
      warn "Please install Rust manually: https://www.rust-lang.org/tools/install"
      return 1
      ;;
  esac

  if have_cmd cargo; then
    say "cargo installed: $(cargo --version)"
  else
    err "cargo still not found after attempted installation. Please install manually."
    return 1
  fi
}

install_lychee() {
  if have_cmd lychee; then
    say "lychee already installed: $(lychee --version)"
    return
  fi

  if ! have_cmd cargo; then
    say "cargo not found; attempting to install Rust toolchain to build lychee..."
    install_rust_toolchain_if_needed || {
      warn "Continuing without lychee. You can skip the hook: SKIP=docs-lychee-internal pre-commit run --all-files"
      return
    }
  fi

  say "Installing lychee via cargo..."
  if cargo install lychee; then
    say "lychee installed: $(lychee --version)"
  else
    warn "Failed to install lychee via cargo. You can install manually or skip the hook:
  - cargo install lychee
  - SKIP=docs-lychee-internal pre-commit run --all-files"
  fi
}

install_hooks() {
  if ! have_cmd pre-commit; then
    err "pre-commit is not installed. Cannot install hooks."
    return 1
  fi

  say "Installing pre-commit hooks (commit + pre-push)..."
  pre-commit install
  pre-commit install --hook-type pre-push

  say "Running pre-commit on all files to warm caches (may take a minute)..."
  # If lychee is not available yet, allow skipping that hook to avoid blocking bootstrap.
  if ! have_cmd lychee; then
    warn "lychee not found; running pre-commit without 'docs-lychee-internal' for now."
    if ! SKIP=docs-lychee-internal pre-commit run --all-files; then
      warn "Pre-commit reported issues. Fix them and re-run:
  pre-commit run --all-files"
    fi
  else
    # Do not fail the whole setup if hooks fail; users can fix and re-run.
    if ! pre-commit run --all-files; then
      warn "Pre-commit reported issues. Fix them and re-run:
  pre-commit run --all-files"
    fi
  fi
}

main() {
  say "Starting dev setup..."

  install_pre_commit
  install_lychee
  install_hooks

  say "Dev setup complete."
  say "Tips:"
  say " - If lychee is unavailable, skip its hook temporarily:"
  say "     SKIP=docs-lychee-internal pre-commit run --all-files"
  say " - Install pre-commit via uv if needed:"
  say "     uv tool install pre-commit"
  say " - To re-run hooks on all files:"
  say "     pre-commit run --all-files"
}

main "$@"
