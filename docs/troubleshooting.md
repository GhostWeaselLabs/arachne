# Troubleshooting

Common issues
- uv not installed: install uv, then uv lock && uv sync
- Import errors: ensure running via uv run; tests set pythonpath to include src
- Type mismatches: check PortSpec.schema matches Message.payload
- Queue full: adjust capacity or select policy (latest/coalesce) as needed

Debugging
- Enable debug logs in observability config
- Use metrics to inspect edge depths and drops
