"""Flask application for docker-stats.

Assembled from the project skeleton by _tools/build.py.  The wiring the skeleton
cannot express lives here: an absolute template folder, an instance folder that
exists before SQLAlchemy resolves the relative sqlite path, and the two HTML
pages (dashboard, alerts) that read the real snapshots/alerts tables.

IMPORTANT: nothing on a GET path touches the Docker socket.  GET / renders from
the snapshots already stored in sqlite and degrades to an empty state; sampling
the daemon is an explicit action (POST /poll, or GET /api/containers) so a
missing /var/run/docker.sock can never hang a page render.
"""
import shutil

from .models import Alert, Snapshot, db
from .stats.api import bp
from .stats.collector import poll
from .stats.history import series

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from . import paths

paths.ensure_runtime_dirs()

def build_app():
    """Build the application: configuration, database, then routes."""
    app = Flask(__name__, template_folder=str(paths.TEMPLATES_DIR),
                instance_path=str(paths.INSTANCE_DIR))
    app.secret_key = "dockerstats-dev"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(paths.INSTANCE_DIR / "dockerstats.db")
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(bp)

    def _latest_by_container():
        """Newest stored snapshot per container.  Pure sqlite read."""
        latest = {}
        for row in Snapshot.query.order_by(Snapshot.id.desc()).limit(2000).all():
            latest.setdefault(row.container, row)
        return latest

    @app.get("/")
    def index():
        latest = _latest_by_container()
        alerts = Alert.query.order_by(Alert.id).all()
        focus = next(iter(sorted(latest.items())), None)
        chart = []
        if focus:
            chart = series(focus[0], 60)[-24:]
        top = max([c["cpu"] or 0 for c in chart], default=0) or 1
        return render_template("index.html", latest=latest, alerts=alerts,
                               focus=focus[0] if focus else None, chart=chart,
                               chart_peak=top,
                               docker_cli=shutil.which("docker"),
                               snapshots=Snapshot.query.count())

    @app.get("/alerts")
    def alerts():
        rules = Alert.query.order_by(Alert.id).all()
        containers = sorted({r.container for r in Snapshot.query.with_entities(Snapshot.container).all()})
        return render_template("alerts.html", rules=rules, containers=containers)

    @app.post("/alerts")
    def alert_create():
        """HTML equivalent of POST /api/alerts (which requires a JSON body)."""
        a = Alert(container=(request.form.get("container") or "").strip(),
                  metric=request.form.get("metric") or "cpu",
                  threshold=request.form.get("threshold", type=float) or 90.0,
                  notify=request.form.get("notify") or "telegram")
        if not a.container:
            flash("container name required", "no")
            return redirect(url_for("alerts"))
        db.session.add(a)
        db.session.commit()
        flash("alert #%d created: %s %s > %s" % (a.id, a.container, a.metric, a.threshold))
        return redirect(url_for("alerts"))

    @app.post("/poll")
    def poll_now():
        """Explicit daemon sample.  This is the only HTML path that talks to Docker,
        and it is a deliberate user action, never part of a page render."""
        try:
            data = poll()
        except Exception as exc:
            flash("docker daemon unreachable (%s: %s) — nothing sampled"
                  % (type(exc).__name__, exc), "no")
            return redirect(url_for("index"))
        for c in data:
            db.session.add(Snapshot(container=c["container"], cpu=c["cpu"], mem=c["mem"],
                                    net_in=c["net_in"], net_out=c["net_out"]))
        db.session.commit()
        flash("sampled %d container(s)" % len(data))
        return redirect(url_for("index"))

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "snapshots": Snapshot.query.count(),
                        "alerts": Alert.query.count()})

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000)

    return app

app = build_app()
