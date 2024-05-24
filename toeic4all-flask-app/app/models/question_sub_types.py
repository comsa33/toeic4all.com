from .. import db


class GeneratedQuestionSubType(db.Model):
    __tablename__ = 'generated_question_sub_types'

    id = db.Column(db.Integer, primary_key=True)
    name_kor = db.Column(db.String)
    name_eng = db.Column(db.String)
    explanation = db.Column(db.String)
    question_type_id = db.Column(db.Integer, db.ForeignKey('generated_question_types.id'))
