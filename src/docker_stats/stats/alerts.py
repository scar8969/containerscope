from datetime import datetime, timedelta


def check_thresholds(snapshot):
    from ..models import Alert, db

    fired = []
    now = datetime.utcnow()
    for a in Alert.query.all():
        value = snapshot.get(a.metric, 0)
        if value >= a.threshold:
            if not a.last_fired or now - a.last_fired > timedelta(minutes=5):
                a.last_fired = now
                fired.append(
                    {
                        "container": a.container,
                        "metric": a.metric,
                        "value": value,
                        "threshold": a.threshold,
                    }
                )
    db.session.commit()
    return fired
