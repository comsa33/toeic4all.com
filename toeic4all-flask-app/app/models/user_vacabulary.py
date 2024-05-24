from .. import db


class UserVocabulary(db.Model):
    __tablename__ = 'user_vocabularies'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    word_id = db.Column(db.Integer, db.ForeignKey('generated_vocabularies.id'))
    wrong_count = db.Column(db.Integer, default=0)

    word = db.relationship('GeneratedVocabulary', backref='user_vocabularies')
