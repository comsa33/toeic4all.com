from .. import db


class GeneratedQuestion(db.Model):
    __tablename__ = 'generated_questions'

    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String)
    question_type_id = db.Column(db.Integer, db.ForeignKey('generated_question_types.id'))
    question_sub_type_id = db.Column(db.Integer, db.ForeignKey('generated_question_sub_types.id'))
    question_level = db.Column(db.Integer)
    translation = db.Column(db.String)
    explanation = db.Column(db.String)
