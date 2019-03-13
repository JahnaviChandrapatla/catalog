import sys
import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
Base = declarative_base()


class GmailUser(Base):
    __tablename__ = 'gmailuser'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    email = Column(String(205), nullable=False)


class Television(Base):
    __tablename__ = 'television'
    id = Column(Integer, primary_key=True)
    name = Column(String(333), nullable=False)
    user_id = Column(Integer, ForeignKey('gmailuser.id'))
    gmailuser = relationship(GmailUser, backref="television")

    @property
    def serialize(self):
        """Return objects data in easily serializeable formats"""
        return {
            'name': self.name,
            'id': self.id
        }


class Tvlist(Base):
    __tablename__ = 'tvlist'
    id = Column(Integer, primary_key=True)
    tvtypes = Column(String(255), nullable=False)
    description = Column(String(555))
    price = Column(String(900))
    rating = Column(String(150))
    inches = Column(String(1000))
    date = Column(DateTime, nullable=False)
    televisionid = Column(Integer, ForeignKey('television.id'))
    television = relationship(
        Television, backref=backref('tvlist', cascade='all, delete'))
    user_id = Column(Integer, ForeignKey('gmailuser.id'))
    gmailuser = relationship(GmailUser, backref="tvlist")

    @property
    def serialize(self):
        """Return objects data in easily serializeable formats"""
        return {
            'tvtypes': self. tvtypes,
            'description': self. description,
            'price': self. price,
            'rating': self. rating,
            'inches': self. inches,
            'date': self. date,
            'id': self. id
        }

engin = create_engine('sqlite:///television.db')
Base.metadata.create_all(engin)
