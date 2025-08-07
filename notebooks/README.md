# Meridian Runtime Notebooks

This directory contains interactive Jupyter notebooks for learning, exploring, and developing with Meridian Runtime. All notebooks are compatible with both Jupyter Lab/Notebook and can be run as Python scripts using Jupytext.

## Tutorials

* [Getting Started](./tutorials/01-getting-started.ipynb): An introduction to the core concepts of Meridian Runtime.
* [Backpressure Policies](./tutorials/02-backpressure-policies.ipynb): A demonstration of the different backpressure policies available in Meridian Runtime.
* [Control-Plane Priorities](./tutorials/03-control-plane-priorities.ipynb): A demonstration of how to use control-plane messages to prioritize critical operations.
* [Observability Basics](./tutorials/04-observability-basics.ipynb): An introduction to the observability features in Meridian Runtime.

## Examples

* [Hello, Graph! (Interactive)](./examples/hello-graph-interactive.ipynb): An interactive version of the `hello-graph` example.
* [Minimal Hello World](./examples/minimal-hello.ipynb): A minimal "Hello World" example demonstrating core concepts.
* [Pipeline Demo (Interactive)](./examples/pipeline-demo-interactive.ipynb): A demonstration of a data processing pipeline with validation, transformation, and a kill switch.
* [Sentiment Analysis Pipeline (Interactive)](./examples/sentiment-interactive.ipynb): A real-time sentiment analysis pipeline with interactive controls.
* [Streaming Coalesce Demo (Interactive)](./examples/streaming-coalesce-interactive.ipynb): A demonstration of the `Coalesce` backpressure policy for merging messages.

## Getting Started

### Prerequisites

1. **Install notebook dependencies:**
   ```bash
   uv sync --extra notebooks
   ```

2. **Start Jupyter:**
   ```bash
   uv run jupyter lab
   # or
   uv run jupyter notebook
   ```

3. **Navigate to notebooks directory:**
   ```bash
   cd notebooks
   ```

### Learning Path

1. **Start with tutorials/** - Begin with `01-getting-started.ipynb`
2. **Explore examples/** - Interactive versions of production examples
3. **Advanced research/** - Performance analysis and prototyping tools

## Notebook Categories

### Tutorials (`tutorials/`)
- **01-getting-started.ipynb**: Basic concepts and first graph
- **02-backpressure-policies.ipynb**: Interactive policy exploration
- **03-control-plane-priorities.ipynb**: Priority and control flow
- **04-observability-basics.ipynb**: Logs, metrics, and tracing

### Examples (`examples/`)
- **hello-graph-interactive.ipynb**: Interactive version of the hello-graph example
- **minimal-hello.ipynb**: Minimal "Hello World" example demonstrating core concepts
- **pipeline-demo-interactive.ipynb**: Data processing pipeline with validation, transformation, and kill switch
- **sentiment-interactive.ipynb**: Real-time sentiment analysis pipeline with interactive controls
- **streaming-coalesce-interactive.ipynb**: Demonstration of the Coalesce backpressure policy

## Running Notebooks

### As Jupyter Notebooks
```bash
uv run jupyter lab
# Open any .ipynb file
```

### As Python Scripts
```bash
# Run directly as Python
uv run python notebooks/examples/minimal-hello.py

# Convert to notebook format
uv run jupytext --to notebook notebooks/examples/minimal-hello.py
```

## Technical Notes

### Performance
- Use shorter timeouts for interactive experiments

### Getting Help
- Check the main documentation: https://ghostweasellabs.github.io/meridian-runtime/
- Review existing examples in `examples/` directory
- Open an issue for notebook-specific problems

## Contributing

When adding new notebooks:
1. Follow the existing structure and naming conventions
2. Include clear setup and cleanup sections
3. Add appropriate documentation and explanations
4. Test with different user types and gather feedback
5. Keep notebooks self-contained and reproducible
