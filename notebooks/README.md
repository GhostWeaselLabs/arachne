# Meridian Runtime Jupyter Notebooks

This directory contains interactive Jupyter notebooks for learning, exploring, and developing with Meridian Runtime.

## Directory Structure

```
notebooks/
├── tutorials/          # Step-by-step learning notebooks
├── examples/           # Interactive versions of existing examples
├── research/           # Advanced analysis and prototyping tools
├── requirements.txt    # Notebook-specific dependencies
└── README.md          # This file
```

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
- **sentiment-pipeline-interactive.ipynb**: Real-time sentiment analysis
- **streaming-coalesce-demo.ipynb**: Burst handling and coalescing
- **performance-benchmarks.ipynb**: Interactive performance testing
- **policy-comparison.ipynb**: Side-by-side policy analysis

### Research (`research/`)
- **performance-profiling.ipynb**: Deep performance analysis
- **observability-analysis.ipynb**: Advanced observability exploration
- **graph-topology-explorer.ipynb**: Interactive graph visualization

## Key Features

### Interactive Visualizations
- Real-time graph topology diagrams
- Queue depth and backpressure visualization
- Message flow animation and tracing
- Interactive parameter tuning with sliders

### Performance Analysis
- Interactive benchmarks with configurable parameters
- Real-time throughput and latency charts
- Policy comparison with side-by-side metrics
- Bottleneck identification and analysis

### Observability Dashboards
- Live Prometheus metrics visualization
- Interactive log filtering and analysis
- Trace visualization with network graphs
- Error rate monitoring and alerting

## Development Guidelines

### Notebook Best Practices
- Keep cells focused and well-documented
- Use markdown cells for explanations
- Include clear setup and cleanup sections
- Handle graceful shutdown for long-running experiments

### Integration with Examples
- Notebooks complement existing `examples/` directory
- Maintain consistency with command-line examples
- Provide interactive alternatives to static documentation

### Performance Considerations
- Jupyter adds overhead - use for learning, not production
- Keep experiments short and focused
- Use appropriate timeouts and cleanup

## Troubleshooting

### Common Issues
- **Import errors**: Ensure `uv sync --extra notebooks` was run
- **Kernel issues**: Restart kernel if graphs don't clean up properly
- **Performance**: Use shorter timeouts for interactive experiments

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
