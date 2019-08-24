from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, index=True)

    def __repr__(self):
        return "<Author(id='{id}', name='{name}')>".format(id=self.id, name=self.name)


article_authors = Table(
    "article_authors",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)


class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    path = Column(String(255), index=True)
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return "<Image(id='{id}', path='{path}')>".format(id=self.id, path=self.path)


article_images = Table(
    "article_images",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, index=True)

    def __repr__(self):
        return "<Tag(id='{id}', name='{name}')>".format(id=self.id, name=self.name)


article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    slug = Column(String(255), index=True)
    title = Column(String(255), index=True)
    content = Column(Text, nullable=True)
    status = Column(CHAR(1), index=True)
    published = Column(DateTime, nullable=True)
    # relationships
    authors = relationship(
        "Author",
        secondary=article_authors,
        backref=backref("authors", lazy="dynamic"),
        lazy="dynamic",
    )
    tags = relationship(
        "Tag",
        secondary=article_tags,
        backref=backref("tags", lazy="dynamic"),
        lazy="dynamic",
    )
    images = relationship(
        "Image",
        secondary=article_images,
        backref=backref("images", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return "<Article(id='{id}', title='{title}')>".format(
            id=self.id, title=self.title
        )
