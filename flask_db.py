from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class Text(db.Model):
    __tablename__ = "texts"
    # __table_args__ = (PrimaryKeyConstraint('author_id', 'article_id'),)

    text_id = db.Column('text_id', db.Integer, primary_key=True)
    title = db.Column('title', db.Text)
    filename = db.Column('filename', db.Text)

    sentences = relationship("Sentence", back_populates="text")


class Sentence(db.Model):
    __tablename__ = "sentences"
    # __table_args__ = (PrimaryKeyConstraint('author_id', 'article_id'),)

    sentence_id = db.Column('sentence_id', db.Integer, primary_key=True)
    lang = db.Column('lang', db.Text)
    # full_text = db.Column('full_text', db.Text)
    translation = db.Column('translation', db.Text)

    text_id = db.Column(db.Integer, ForeignKey('texts.text_id'))
    text = relationship("Text", back_populates="sentences", uselist=False)

    words = relationship("Word", back_populates="sentence")
    

    # Внешний ключ, ссылающийся на text_id в таблице texts

    # # Связь с таблицей Text
    # text = db.relationship("Text", back_populates="sentences")


class Word(db.Model):
    __tablename__ = "words"

    word_id = db.Column('word_id', db.Integer, primary_key=True)
    form = db.Column('form', db.Text)
    pos = db.Column('pos', db.Text)

    off_start = db.Column("off_start", db.Integer)
    off_end = db.Column("off_end", db.Integer)
    next_word = db.Column("next_word", db.Integer)
    sentence_index = db.Column("sentence_index", db.Integer)
    sentence_index_neg = db.Column("sentence_index_neg", db.Integer)

    sentence_id = db.Column(db.Integer, ForeignKey('sentences.sentence_id'))
    sentence = relationship("Sentence", back_populates="words")

    # TODO:
    glosses = relationship("Gloss", back_populates="word")


class PossibleGloss(db.Model):
    __tablename__ = "possible_glosses"
    __table_args__ = (UniqueConstraint('meaning', 'allomorph'),)

    possible_gloss_id = db.Column('possible_gloss_id', db.Integer, primary_key=True)
    meaning = db.Column('meaning', db.Text)
    allomorph = db.Column('allomorph', db.Text)


class PossibleStem(db.Model):
    __tablename__ = "possible_stems"
    __table_args__ = (UniqueConstraint('meaning', 'allomorph'),)

    possible_stem_id = db.Column('possible_stem_id', db.Integer, primary_key=True)
    meaning = db.Column('meaning', db.Text)         # русский перевод
    allomorph = db.Column('allomorph', db.Text)



class Gloss(db.Model):
    __tablename__ = "glosses"

    gloss_id = db.Column('gloss_id', db.Integer, primary_key=True)

    # каждая глосса это либо STEM, и тогда у неё есть possible_stem_id и нет possible_gloss_id
    #   либо не STEM, и тогда у неё есть possible_gloss_id и нет possible_stem_id
    possible_gloss_id = db.Column(db.Integer, ForeignKey('possible_glosses.possible_gloss_id'))
    possible_stem_id = db.Column(db.Integer, ForeignKey('possible_stems.possible_stem_id'))

    word_id = db.Column(db.Integer, ForeignKey('words.word_id'))
    word = relationship("Word", back_populates="glosses", uselist=False)

