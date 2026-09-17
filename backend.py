"""Robot Invites simulation backend and small HTTP API."""
from __future__ import annotations

import json
import math
import random
import time
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

ROOT = Path(__file__).parent


@dataclass
class Robot:
    robot_id: int
    x: float
    y: float
    status: str = "waiting"
    arrival_time: float = 0.0
    entered_time: float | None = None
    punctuality: float = 1.0


class Simulation:
    """Discrete-time overhead simulation using robot-width door packing."""

    def __init__(self, seed: int = 7):
        self.lock = Lock()
        self.seed = seed
        self.random = random.Random(seed)
        self.reset()

    def reset(self, robot_count: int = 30, door_width: float = 3.0, door_height: float = 1.4,
              robot_width: float = 1.0, robot_height: float = 1.0,
              extra_doors: int = 0, variability: float = 0.0,
              arrival_pattern: str = "default"):
        with self.lock:
            self.random.seed(self.seed)
            self.time = 0.0
            self.running = False
            self.log: list[dict] = []
            self.log_path = ROOT / "simulation.jsonl"
            self.log_path.write_text("", encoding="utf-8")
            self.config = {
                "robot_count": max(1, min(200, int(robot_count))),
                "door_width": max(1.0, float(door_width)),
                "door_height": max(1.0, float(door_height)),
                "robot_width": max(0.25, float(robot_width)),
                "robot_height": max(0.25, float(robot_height)),
                "extra_doors": max(0, min(5, int(extra_doors))),
                "variability": max(0.0, min(1.0, float(variability))),
                "arrival_pattern": arrival_pattern,
            }
            self.robots = []
            for robot_id in range(self.config["robot_count"]):
                punctuality = self.random.uniform(1.0 - self.config["variability"],
                                                   1.0 + self.config["variability"])
                arrival_time = robot_id * 0.25 * punctuality
                if arrival_pattern == "scheduled":
                    arrival_time = robot_id / max(1, self.config["robot_count"] - 1) * 7.0
                elif arrival_pattern == "personality":
                    arrival_time = self.random.uniform(0.0, 3.5)
                elif arrival_pattern == "surge":
                    arrival_time = 0.0
                self.robots.append(Robot(robot_id, -4.0, self._queue_y(robot_id),
                                         arrival_time=arrival_time,
                                         punctuality=punctuality))
            self._record("reset")

    def _queue_y(self, index: int) -> float:
        return 1.6 + (index % 12) * (self.config["robot_height"] + 0.25)

    @property
    def capacity_per_tick(self) -> int:
        width_capacity = max(1, math.floor(self.config["door_width"] / self.config["robot_width"] + 1e-9))
        return width_capacity * (self.config["extra_doors"] + 1)

    def step(self, seconds: float = 0.25) -> dict:
        with self.lock:
            seconds = max(0.01, min(2.0, float(seconds)))
            self.time += seconds
            active = [robot for robot in self.robots if robot.status == "waiting" and robot.arrival_time <= self.time]
            active.sort(key=lambda robot: robot.robot_id)
            entering = active[: self.capacity_per_tick]
            for robot in entering:
                robot.status = "inside"
                robot.entered_time = self.time
                robot.x = 0.0
                robot.y = 0.25 + (robot.robot_id % 10) * (self.config["robot_height"] + 0.2)
            for robot in self.robots:
                if robot.status == "waiting":
                    robot.x = min(-4.0 + max(0.0, self.time - robot.arrival_time) * 0.55, -1.0)
            self._record("step")
            return self.state()

    def run(self, seconds: float = 0.25) -> dict:
        self.running = bool(seconds)
        return self.step(seconds)

    def _record(self, event: str):
        inside = [robot for robot in self.robots if robot.status == "inside"]
        waiting = [robot for robot in self.robots if robot.status == "waiting" and robot.arrival_time <= self.time]
        arrived = [robot for robot in self.robots if robot.arrival_time <= self.time]
        waits = [robot.entered_time - robot.arrival_time for robot in inside if robot.entered_time is not None]
        entry_rate = len(inside) / self.time if self.time else 0.0
        row = {
            "time": round(self.time, 3),
            "event": event,
            "inside": len(inside),
            "waiting": len(waiting),
            "not_yet_arrived": self.config["robot_count"] - len(arrived),
            "throughput_per_minute": round(entry_rate * 60.0, 3),
            "average_wait": round(sum(waits) / len(waits), 3) if waits else 0.0,
            "max_wait": round(max(waits), 3) if waits else 0.0,
            "door_capacity": self.capacity_per_tick,
            "utilization": round(len(inside) / self.config["robot_count"], 3),
        }
        self.log.append(row)
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(row) + "\n")

    def state(self) -> dict:
        latest = self.log[-1] if self.log else {}
        return {
            "time": round(self.time, 3),
            "running": self.running,
            "config": self.config,
            "door_capacity": self.capacity_per_tick,
            "robots": [asdict(robot) for robot in self.robots],
            "metrics": latest,
            "log_length": len(self.log),
        }


simulation = Simulation()


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, status=200, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else (
            json.dumps(payload).encode("utf-8") if content_type == "application/json" else payload.encode("utf-8")
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/state":
            return self._send(simulation.state())
        if path == "/api/log":
            return self._send({"config": simulation.config, "rows": simulation.log})
        if path in ("/", "/index.html"):
            return self._send((ROOT / "index.html").read_bytes(), content_type="text/html; charset=utf-8")
        if path == "/sketch.js":
            return self._send((ROOT / "sketch.js").read_bytes(), content_type="application/javascript")
        if path == "/style.css":
            return self._send((ROOT / "style.css").read_bytes(), content_type="text/css")
        return self._send({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        size = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(size) or b"{}")
        except json.JSONDecodeError:
            return self._send({"error": "invalid JSON"}, 400)
        if path == "/api/reset":
            simulation.reset(**body)
            return self._send(simulation.state())
        if path == "/api/step":
            return self._send(simulation.step(body.get("seconds", 0.25)))
        return self._send({"error": "not found"}, 404)

    def log_message(self, *_args):
        return


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Robot Invites running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
