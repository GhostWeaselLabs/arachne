# Meridian Runtime Makefile
#
# Quick commands for running example demos and common developer tasks.
#
# Usage:
#   make help
#   make demo-sentiment
#   make demo-coalesce
#   make demo-sentiment-debug
#   make demo-coalesce-quiet
#   make docs-build
#   make docs-serve
#   make docs-check-links
#
# Notes:
# - These targets assume your shell is positioned at the repository root.
# - Python should be available in your current environment (venv recommended).
# - Override defaults with environment variables, e.g.:
#     RATE_HZ=20 TICK_MS=10 make demo-sentiment

SHELL := /bin/sh
PYTHON ?= python

# Common demo parameters (can be overridden at invocation)
RATE_HZ ?= 8.0
CONTROL_PERIOD ?= 4.0
KEEP ?= 10
TICK_MS ?= 25
MAX_BATCH ?= 8
TIMEOUT_S ?= 6.0
CAP_TEXT ?= 64
CAP_TOKENS ?= 64
CAP_SCORED ?= 128
CAP_CONTROL ?= 8

COAL_RATE_HZ ?= 300.0
COAL_TICK_MS ?= 10
COAL_MAX_BATCH ?= 16
COAL_TIMEOUT_S ?= 5.0
CAP_SENSOR_TO_AGG ?= 256
CAP_AGG_TO_SINK ?= 16
COAL_KEEP ?= 10

.PHONY: help
help:
	@echo "Meridian Runtime - Makefile"
	@echo
	@echo "Available targets:"
	@echo "  help                     Show this help"
	@echo "  demo-minimal             Run the minimal hello world demo"
	@echo "  demo-sentiment           Run the sentiment pipeline demo"
	@echo "  demo-sentiment-debug     Run the sentiment demo with --debug"
	@echo "  demo-coalesce            Run the streaming coalesce demo"
	@echo "  demo-coalesce-quiet      Run the coalesce demo with --quiet"
	@echo "  docs-clean               Clean the built site directory"
	@echo "  docs-build               Build the MkDocs site to ./site"
	@echo "  docs-serve               Serve the docs locally with live reload"
	@echo "  docs-check-links         Check links in docs and README using lychee"
	@echo
	@echo "Override parameters with environment variables. Examples:"
	@echo "  RATE_HZ=20 TICK_MS=10 make demo-sentiment"
	@echo "  COAL_RATE_HZ=600 CAP_AGG_TO_SINK=8 make demo-coalesce"
	@echo

# --------------------------------------------------------------------
# Minimal Hello World demo
# --------------------------------------------------------------------
.PHONY: demo-minimal
demo-minimal:
	$(PYTHON) examples/minimal_hello/main.py

# --------------------------------------------------------------------
# Sentiment demo
# --------------------------------------------------------------------
.PHONY: demo-sentiment
demo-sentiment:
	$(PYTHON) examples/sentiment/main.py --human \
		--rate-hz $(RATE_HZ) \
		--control-period $(CONTROL_PERIOD) \
		--keep $(KEEP) \
		--tick-ms $(TICK_MS) \
		--max-batch $(MAX_BATCH) \
		--timeout-s $(TIMEOUT_S) \
		--cap-text $(CAP_TEXT) \
		--cap-tokens $(CAP_TOKENS) \
		--cap-scored $(CAP_SCORED) \
		--cap-control $(CAP_CONTROL)

.PHONY: demo-sentiment-debug
demo-sentiment-debug:
	$(PYTHON) examples/sentiment/main.py --human --debug \
		--rate-hz $(RATE_HZ) \
		--control-period $(CONTROL_PERIOD) \
		--keep $(KEEP) \
		--tick-ms $(TICK_MS) \
		--max-batch $(MAX_BATCH) \
		--timeout-s $(TIMEOUT_S) \
		--cap-text $(CAP_TEXT) \
		--cap-tokens $(CAP_TOKENS) \
		--cap-scored $(CAP_SCORED) \
		--cap-control $(CAP_CONTROL)

# --------------------------------------------------------------------
# Streaming coalesce demo
# --------------------------------------------------------------------
.PHONY: demo-coalesce
demo-coalesce:
	$(PYTHON) examples/streaming_coalesce/main.py --human \
		--rate-hz $(COAL_RATE_HZ) \
		--tick-ms $(COAL_TICK_MS) \
		--max-batch $(COAL_MAX_BATCH) \
		--timeout-s $(COAL_TIMEOUT_S) \
		--cap-sensor-to-agg $(CAP_SENSOR_TO_AGG) \
		--cap-agg-to-sink $(CAP_AGG_TO_SINK) \
		--keep $(COAL_KEEP)

.PHONY: demo-coalesce-quiet
demo-coalesce-quiet:
	$(PYTHON) examples/streaming_coalesce/main.py --human --quiet \
		--rate-hz $(COAL_RATE_HZ) \
		--tick-ms $(COAL_TICK_MS) \
		--max-batch $(COAL_MAX_BATCH) \
		--timeout-s $(COAL_TIMEOUT_S) \
		--cap-sensor-to-agg $(CAP_SENSOR_TO_AGG) \
		--cap-agg-to-sink $(CAP_AGG_TO_SINK) \
		--keep $(COAL_KEEP)

# --------------------------------------------------------------------
# Documentation (MkDocs)
# --------------------------------------------------------------------
.PHONY: docs-clean
docs-clean:
	rm -rf site/

.PHONY: docs-build
docs-build: docs-clean
	@which mkdocs >/dev/null 2>&1 || (echo "mkdocs not found. Install with: pip install mkdocs mkdocs-material" && exit 1)
	mkdocs build --strict

.PHONY: docs-serve
docs-serve:
	@which mkdocs >/dev/null 2>&1 || (echo "mkdocs not found. Install with: pip install mkdocs mkdocs-material" && exit 1)
	mkdocs serve -a 127.0.0.1:8000

.PHONY: docs-check-links
docs-check-links:
	@which lychee >/dev/null 2>&1 || (echo "lychee not found. Install with: cargo install lychee" && exit 1)
	lychee --no-progress --max-concurrency 8 --exclude-all-private --accept 200,429 --retry-wait-time 2 --retry-count 2 --timeout 20 --base ./ .
