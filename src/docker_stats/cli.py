"""docker-stats — command line over stats/collector.py and stats/history.py.

The docker SDK is an install-time dependency, so it is imported lazily inside the
subcommands: `--help` must work on a bare interpreter.
"""

import argparse
import sys

from . import paths


def _db():
    """Open the SQLite session lazily (Flask-SQLAlchemy is not needed for --help)."""
    from flask import Flask

    from .models import db

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(
        paths.INSTANCE_DIR / "dockerstats.db"
    )
    db.init_app(app)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    return db


def cmd_ps(_args):
    from .stats.collector import poll

    try:
        rows = poll()
    except Exception as e:
        print(f"error: docker daemon unreachable ({e})", file=sys.stderr)
        return 1
    if not rows:
        print("no running containers")
        return 0
    print(f"{'container':<24} {'cpu%':>7} {'mem':>12} {'net_in':>14} {'net_out':>14}  status")
    for c in rows:
        print(
            f"{c['container']:<24} {c['cpu']:>7} {c['mem']:>12} {c['net_in']:>14} "
            f"{c['net_out']:>14}  {c['status']}"
        )
    return 0


def cmd_history(args):
    from .stats.history import series

    _db()
    rows = series(args.container, args.minutes)
    if not rows:
        print(f"no samples for {args.container} in the last {args.minutes}m")
        return 0
    for r in rows:
        print(f"{r['t']}  cpu={r['cpu']}  mem={r['mem']}")
    return 0


def cmd_alerts(_args):
    from .models import Alert

    _db()
    rows = Alert.query.all()
    if not rows:
        print("no alert rules")
        return 0
    for a in rows:
        fired = a.last_fired.isoformat() if a.last_fired else "-"
        print(
            f"{a.id:<4} {a.container:<24} {a.metric:<8} >= {a.threshold:<8} "
            f"notify={a.notify:<10} last_fired={fired}"
        )
    return 0


def main():
    p = argparse.ArgumentParser(prog="docker-stats")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("ps", help="poll the docker daemon once and print live stats")
    h = sub.add_parser("history", help="print recorded samples for one container")
    h.add_argument("container")
    h.add_argument("--minutes", type=int, default=60)
    sub.add_parser("alerts", help="list alert rules")
    args = p.parse_args()
    if args.cmd == "ps":
        return cmd_ps(args)
    if args.cmd == "history":
        return cmd_history(args)
    if args.cmd == "alerts":
        return cmd_alerts(args)
    p.print_help()
    return 1
