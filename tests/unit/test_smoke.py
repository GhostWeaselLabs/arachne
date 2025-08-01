# Unit smoke tests for Arachne package


def test_import_arachne_package():
    # Verify that the package can be imported and exposes expected attributes
    import arachne  # noqa: F401

    assert hasattr(arachne, "__version__"), "Arachne package should expose __version__"
    # Basic sanity on optional namespaces/symbols
    assert hasattr(arachne, "Message")
    assert hasattr(arachne, "Node")
    assert hasattr(arachne, "Subgraph")
    assert hasattr(arachne, "Scheduler")


def test_version_is_semverish():
    import arachne

    version = getattr(arachne, "__version__", None)
    assert isinstance(version, str) and version, "__version__ must be a non-empty string"

    # Very lightweight semantic-ish validation: MAJOR.MINOR.PATCH or 0.0.0 for bootstrap
    parts = version.split(".")
    assert 1 <= len(parts) <= 3, "Version should have 1-3 dot-separated components"
    # Ensure each component is numeric when present (e.g., "0", "0", "0")
    for p in parts:
        assert p.isdigit(), f"Version component '{p}' should be numeric"
