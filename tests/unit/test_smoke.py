# Unit smoke tests for Meridian Runtime package


def test_import_meridian_package():
    # Verify that the package can be imported and exposes expected attributes
    import meridian  # noqa: F401

    assert hasattr(meridian, "__version__"), "Meridian package should expose __version__"
    # Basic sanity on optional namespaces/symbols
    assert hasattr(meridian, "Message")
    assert hasattr(meridian, "Node")
    assert hasattr(meridian, "Subgraph")
    assert hasattr(meridian, "Scheduler")


def test_version_is_semverish_for_meridian():
    import meridian

    version = getattr(meridian, "__version__", None)
    assert isinstance(version, str) and version, "__version__ must be a non-empty string"

    # Very lightweight semantic-ish validation: MAJOR.MINOR.PATCH or 0.0.0 for bootstrap
    parts = version.split(".")
    assert 1 <= len(parts) <= 3, "Version should have 1-3 dot-separated components"
    # Ensure each component is numeric when present (e.g., "0", "0", "0")
    for p in parts:
        assert p.isdigit(), f"Version component '{p}' should be numeric"
