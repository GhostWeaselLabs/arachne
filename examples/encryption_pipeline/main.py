from __future__ import annotations

import json
import threading
import time

from meridian.core import Scheduler, SchedulerConfig, Subgraph
from meridian.nodes import (
    DataProducer,
    EncryptionAlgorithm,
    EncryptionMode,
    EncryptionNode,
    MapTransformer,
)


def build_graph() -> Subgraph:
    # Producer emits one dict
    p = DataProducer("p", data_source=lambda: iter([{ "hello": "world" }]), interval_ms=0)
    key = b"0" * 32
    enc = EncryptionNode("enc", encryption_key=key, algorithm=EncryptionAlgorithm.AES_256_GCM)
    dec = EncryptionNode("dec", encryption_key=key, algorithm=EncryptionAlgorithm.AES_256_GCM, mode=EncryptionMode.DECRYPT)
    decode_json = MapTransformer("decode", transform_fn=lambda b: json.loads(b.decode("utf-8")))

    g = Subgraph.from_nodes("crypto", [p, enc, dec, decode_json])
    g.connect(("p", "output"), ("enc", "input"))
    g.connect(("enc", "output"), ("dec", "input"))
    g.connect(("dec", "output"), ("decode", "input"))
    return g


def main() -> None:
    g = build_graph()
    s = Scheduler(SchedulerConfig(idle_sleep_ms=0, tick_interval_ms=5))
    s.register(g)
    th = threading.Thread(target=s.run, daemon=True)
    th.start(); time.sleep(0.2); s.shutdown(); th.join()


if __name__ == "__main__":
    main()
