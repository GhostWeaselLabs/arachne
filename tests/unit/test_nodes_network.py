from __future__ import annotations

import http.server
import socket
import socketserver
import threading
from contextlib import closing

from meridian.core import Message, MessageType
from meridian.nodes import (
    HttpClientNode,
    HttpServerNode,
    MessageQueueNode,
    NodeTestHarness,
    WebSocketNode,
)


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = b"hello"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A003
        return


def test_http_client_node_gets() -> None:
    port = _free_port()
    httpd = socketserver.TCPServer(("127.0.0.1", port), _Handler)
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()

    try:
        client = HttpClientNode("c", base_url=f"http://127.0.0.1:{port}")
        h = NodeTestHarness(client)
        h.node.on_message("input", Message(MessageType.DATA, {"method": "GET", "url": "/"}))
        out = h.get_emitted_messages("output")
        assert out and out[0].payload["status"] == 200
        assert out[0].payload["body"] == "hello"
    finally:
        httpd.shutdown()


def test_http_server_and_websocket_simulations() -> None:
    server = HttpServerNode("s")
    hs = NodeTestHarness(server)
    server.simulate_request("GET", "/health")
    out = hs.get_emitted_messages("output")
    assert out and out[0].payload["path"] == "/health"

    ws = WebSocketNode("ws", url="ws://localhost")
    hw = NodeTestHarness(ws)
    hw.send_message("input", {"say": "hello"})
    ws.simulate_incoming({"msg": "hi"})
    out2 = hw.get_emitted_messages("output")
    assert out2 and out2[0].payload == {"msg": "hi"}


def test_message_queue_node_in_memory() -> None:
    prod = MessageQueueNode("mq-p", queue_type="redis", connection_config={}, queue_name="q", mode="producer")
    cons = MessageQueueNode("mq-c", queue_type="redis", connection_config={}, queue_name="q", mode="consumer")
    hp = NodeTestHarness(prod)
    hc = NodeTestHarness(cons)
    hp.send_message("input", 123)
    hc.trigger_tick()
    out = hc.get_emitted_messages("output")
    assert out and out[0].payload == 123
