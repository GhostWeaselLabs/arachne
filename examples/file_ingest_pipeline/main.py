from __future__ import annotations

import os
import tempfile
import threading
import time

from meridian.core import Scheduler, SchedulerConfig, Subgraph
from meridian.nodes import FileReaderNode, FileWriterNode, MapTransformer


def build_graph(tmp_path: str) -> Subgraph:
    writer = FileWriterNode("writer", file_path=tmp_path)
    # Identity map to log what is written
    log_map = MapTransformer("logger", transform_fn=lambda x: x)
    reader = FileReaderNode("reader", file_path=tmp_path, polling_interval_ms=10)

    g = Subgraph.from_nodes("file_io", [writer, log_map, reader])
    # Note: writer does not emit; we simulate by writing lines then reader picks them up
    return g


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "data.log")
        g = build_graph(path)
        # Fetch writer node
        writer = g.nodes["writer"]
        assert isinstance(writer, FileWriterNode)

        s = Scheduler(SchedulerConfig(idle_sleep_ms=0, tick_interval_ms=5))
        s.register(g)
        th = threading.Thread(target=s.run, daemon=True)
        th.start()

        # Simulate appending lines
        for line in ["a", "b", "c"]:
            writer._handle_message("input", __import__("meridian").core.Message(__import__("meridian").core.MessageType.DATA, line))
        time.sleep(0.2)
        s.shutdown(); th.join()


if __name__ == "__main__":
    main()
