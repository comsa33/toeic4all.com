from datetime import datetime

from .. import db


class UserTestDetail(db.Model):
    __tablename__ = 'user_test_detail'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    test_id = db.Column(db.String)
    test_type = db.Column(db.String)
    test_level = db.Column(db.String)
    question_count = db.Column(db.Integer)
    time_record = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
