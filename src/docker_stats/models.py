from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Snapshot(db.Model):
    __tablename__ = "snapshots"
    id = db.Column(db.Integer, primary_key=True)
    container = db.Column(db.String(128), index=True)
    cpu = db.Column(db.Float, default=0.0)
    mem = db.Column(db.BigInteger, default=0)
    net_in = db.Column(db.BigInteger, default=0)
    net_out = db.Column(db.BigInteger, default=0)
    at = db.Column(db.DateTime, default=datetime.utcnow)

class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    container = db.Column(db.String(128), default="")
    metric = db.Column(db.String(16), default="cpu")
    threshold = db.Column(db.Float, default=90.0)
    notify = db.Column(db.String(32), default="telegram")
    last_fired = db.Column(db.DateTime, nullable=True)
