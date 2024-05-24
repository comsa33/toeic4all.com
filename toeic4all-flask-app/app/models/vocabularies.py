from .. import db


class GeneratedVocabulary(db.Model):
    __tablename__ = 'generated_vocabularies'

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String)
    translation = db.Column(db.String)
    difficulty = db.Column(db.Integer)
    explanation = db.Column(db.String)
    part_of_speech = db.Column(db.String, nullable=True)
    example = db.Column(db.String, nullable=True)
    example_translation = db.Column(db.String, nullable=True)
    question_id = db.Column(db.Integer, db.ForeignKey('generated_questions.id'))
