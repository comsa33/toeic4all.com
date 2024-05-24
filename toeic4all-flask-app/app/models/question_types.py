from .. import db


class GeneratedQuestionType(db.Model):
    __tablename__ = 'generated_question_types'

    id = db.Column(db.Integer, primary_key=True)
    name_kor = db.Column(db.String)
    name_eng = db.Column(db.String)
    explanation = db.Column(db.String)
