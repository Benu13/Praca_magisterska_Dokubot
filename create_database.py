from sqlalchemy import create_engine
import pandas as pd
#engine = create_engine('sqlite://', echo=False)

from sqlalchemy import Column, ForeignKey, Integer, Table, String
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import backref

if __name__ == '__main__':
    df = pd.read_csv("data/tables/metadata_table.csv")
    df2 = df.drop(labels = ['keywords'], axis=1)

    Base = declarative_base()

    class DocType(Base):
        __tablename__ = 'DocType',
        id = Column(Integer, primary_key = True),
        Dtype = Column(String)


    class Document(Base):
        __tablename__ = 'Document',
        id = Column(Integer, primary_key=True),
        title = Column(String),
        authors = Column(String),
        source = Column(String),
        DocType_id = Column(Integer, ForeignKey('DocType.id'))
        DocType = relationship("DocType", backref=backref("DocType", uselist=False))
        Keywords = relationship("Keyword", back_populates="Document")

    class Keyword(Base):
        __tablename__ = 'Keyword',
        id = Column(Integer, primary_key = True),
        Document_id = Column(Integer, ForeignKey("Document.id"))

        Document = relationship("Document", back_populates="Keywords")


    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
