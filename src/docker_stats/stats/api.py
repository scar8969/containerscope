import json
import time

from flask import Blueprint, Response, jsonify, request

from ..models import Alert, Snapshot, db
from .alerts import check_thresholds
from .collector import poll
from .history import append, series

bp = Blueprint("stats", __name__)


@bp.get("/api/containers")
def containers():
    """Live container stats.

    The frozen contract in `openapi/containerscope.yaml` documents 200 for
    this path, so a missing docker daemon is reported *inside* a 200 body as an
    explicit degradation envelope rather than as a 503: the app itself is
    healthy, only one dependency is missing.  No container data is fabricated --
    the list is empty and `reason` carries the real exception text.
    """
    try:
        data = poll()
    except Exception as exc:
        return jsonify(
            {"containers": [], "available": False, "reason": f"{type(exc).__name__}: {exc}"}
        )
    for c in data:
        append(
            Snapshot(
                container=c["container"],
                cpu=c["cpu"],
                mem=c["mem"],
                net_in=c["net_in"],
                net_out=c["net_out"],
            )
        )
    db.session.commit()
    return jsonify({"containers": data})


@bp.get("/api/containers/<name>/stats")
def container_stats(name):
    return jsonify({"series": series(name, request.args.get("minutes", 60, type=int))})


@bp.get("/api/containers/<name>/logs")
def container_logs(name):
    """docker SDK logs tail."""
    tail = request.args.get("tail", 200, type=int)
    try:
        import docker

        client = docker.from_env()
        raw = client.containers.get(name).logs(tail=tail)
    except Exception as exc:
        # Same contract note as containers(): 200 + explicit degradation.
        return jsonify(
            {
                "container": name,
                "tail": tail,
                "lines": [],
                "available": False,
                "reason": f"{type(exc).__name__}: {exc}",
            }
        )
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    return jsonify({"container": name, "tail": tail, "lines": raw.splitlines()})


@bp.post("/api/alerts")
def add_alert():
    d = request.get_json(force=True, silent=True) or {}
    a = Alert(
        container=d.get("container", ""),
        metric=d.get("metric", "cpu"),
        threshold=d.get("threshold", 90.0),
        notify=d.get("notify", "telegram"),
    )
    db.session.add(a)
    db.session.commit()
    return jsonify({"id": a.id})


@bp.get("/api/alerts")
def list_alerts():
    return jsonify(
        {
            "alerts": [
                {
                    "id": a.id,
                    "container": a.container,
                    "metric": a.metric,
                    "threshold": a.threshold,
                    "last_fired": a.last_fired.isoformat() if a.last_fired else "",
                }
                for a in Alert.query.all()
            ]
        }
    )


@bp.get("/api/stream")
def stream():
    """Bounded server-sent events feed.

    ?frames=N    frames to emit before closing (default 3, clamped 1..600)
    ?interval=S  seconds between frames (default 2.0, clamped 0.1..60)

    A bounded response is deliberate: an unbounded `while True` generator never
    lets an HTTP GET complete, which pins a worker for the lifetime of the
    client and makes the endpoint untestable.  The final `event: end` frame
    closes the response; a browser EventSource reconnects on its own.
    """
    try:
        frames = max(1, min(600, int(request.args.get("frames", 3))))
    except (TypeError, ValueError):
        frames = 3
    try:
        interval = min(60.0, max(0.1, float(request.args.get("interval", 2.0))))
    except (TypeError, ValueError):
        interval = 2.0

    def gen():
        sent = 0
        while sent < frames:
            try:
                data = poll()
                fired = []
                for c in data:
                    fired += check_thresholds(c)
                yield f"data: {json.dumps({'containers': data, 'alerts': fired})}\n\n"
            except Exception:
                yield f"data: {json.dumps({'error': 'daemon down'})}\n\n"
            sent += 1
            if sent < frames:
                time.sleep(interval)
        yield "event: end\ndata: {}\n\n"

    return Response(gen(), mimetype="text/event-stream")
