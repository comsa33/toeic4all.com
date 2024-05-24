from .. import db


class GeneratedAnswer(db.Model):
    __tablename__ = 'generated_answers'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    is_correct = db.Column(db.Boolean)
    question_id = db.Column(db.Integer, db.ForeignKey('generated_questions.id'))
