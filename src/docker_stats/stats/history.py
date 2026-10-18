def append(snapshot):
    from ..models import db

    db.session.add(snapshot)
    db.session.commit()


def series(container, minutes=60):
    from datetime import datetime, timedelta

    from ..models import Snapshot

    since = datetime.utcnow() - timedelta(minutes=minutes)
    rows = Snapshot.query.filter(Snapshot.container == container, Snapshot.at >= since).all()
    return [{"t": r.at.isoformat() if r.at else "", "cpu": r.cpu, "mem": r.mem} for r in rows]
