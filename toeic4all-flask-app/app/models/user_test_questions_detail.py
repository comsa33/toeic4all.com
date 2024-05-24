from sqlalchemy import UniqueConstraint

from .. import db


class UserTestQuestionsDetail(db.Model):
    __tablename__ = 'user_test_questions_detail'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('user_test_detail.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('generated_questions.id'))
    is_correct = db.Column(db.Boolean, default=False)
    time_record_per_question = db.Column(db.Integer)

    __table_args__ = (
        UniqueConstraint('question_id', 'test_id'),
    )
