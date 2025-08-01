# Integration smoke tests for Arachne examples
# This is a placeholder to ensure the example shape is invokable and imports resolve.
# As of M1, the runtime primitives are placeholders; this test verifies the scaffolding only.

import importlib
import types


def test_examples_module_exists():
    # The examples package should exist per M1 scaffold.
    # We don't assume specific subpackages beyond presence.
    try:
        mod = importlib.import_module("examples")
    except ModuleNotFoundError as exc:  # pragma: no cover - clearer error
        raise AssertionError("examples package should be present in M1 scaffold") from exc

    assert isinstance(mod, types.ModuleType)


def test_minimal_example_shape():
    # Simulate the minimal example described in README using the placeholder runtime.
    import arachne

    class Producer(arachne.Node):
        def __init__(self, n: int = 3) -> None:
            self._n = n
            self._i = 0

        def name(self) -> str:
            return "producer"

        def outputs(self) -> dict[str, type]:
            return {"out": int}

        def on_start(self) -> None:
            self._i = 0

        def on_tick(self) -> None:
            # In M1, emit is a no-op; this just validates the flow doesn't crash.
            if self._i < self._n:
                arachne.Node.emit(self, "out", arachne.Message(payload=self._i))
                self._i += 1

    class Consumer(arachne.Node):
        def name(self) -> str:
            return "consumer"

        def inputs(self) -> dict[str, type]:
            return {"in": int}

        def on_message(self, port: str, msg: arachne.Message) -> None:
            # No real assertions here; in M1 this is a placeholder.
            _ = (port, msg)

    g = arachne.Subgraph()
    g.add_node(Producer(n=2))
    g.add_node(Consumer())
    g.connect(("producer", "out"), ("consumer", "in"), capacity=4)

    sch = arachne.Scheduler()
    sch.register(g)

    # Placeholder scheduler does nothing; ensure it doesn't crash.
    sch.run()
