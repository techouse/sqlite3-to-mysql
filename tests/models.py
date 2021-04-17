from decimal import Decimal
from os import environ

import sqlalchemy.types as types
from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    BigInteger,
    BLOB,
    Boolean,
    CHAR,
    Date,
    DateTime,
    Integer,
    JSON,
    REAL,
    SmallInteger,
    String,
    Text,
    Time,
    TIMESTAMP,
    VARCHAR,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.functions import current_timestamp


class SQLiteNumeric(types.TypeDecorator):
    impl = types.String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return Decimal(value)


class MyCustomType(types.TypeDecorator):
    impl = types.String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(self.length))

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return str(value)


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


class Misc(Base):
    """This model contains all possible MySQL types"""

    __tablename__ = "misc"
    id = Column(Integer, primary_key=True)
    big_integer_field = Column(BigInteger, default=0)
    blob_field = Column(BLOB, nullable=True, index=True)
    boolean_field = Column(Boolean, default=False)
    char_field = Column(CHAR(255), nullable=True)
    date_field = Column(Date, nullable=True)
    date_time_field = Column(DateTime, nullable=True)
    decimal_field = Column(SQLiteNumeric(10, 2), nullable=True)
    float_field = Column(SQLiteNumeric(12, 4), default=0)
    integer_field = Column(Integer, default=0)
    if environ.get("LEGACY_DB", "0") == "0":
        json_field = Column(JSON, nullable=True)
    numeric_field = Column(SQLiteNumeric(12, 4), default=0)
    real_field = Column(REAL(12, 4), default=0)
    small_integer_field = Column(SmallInteger, default=0)
    string_field = Column(String(255), nullable=True)
    text_field = Column(Text, nullable=True)
    time_field = Column(Time, nullable=True)
    varchar_field = Column(VARCHAR(255), nullable=True)
    timestamp_field = Column(TIMESTAMP, default=current_timestamp())
    my_type_field = Column(MyCustomType(255), nullable=True)


article_misc = Table(
    "article_misc",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("misc_id", Integer, ForeignKey("misc.id"), primary_key=True),
)


class Media(Base):
    __tablename__ = "media"
    id = Column(CHAR(64), primary_key=True)
    title = Column(String(255), index=True)
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return "<Media(id='{id}', title='{title}')>".format(
            id=self.id, title=self.title
        )


article_media = Table(
    "article_media",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("media_id", CHAR(64), ForeignKey("media.id"), primary_key=True),
)


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    hash = Column(String(32), unique=True)
    slug = Column(String(255), index=True)
    title = Column(String(255), index=True)
    content = Column(Text, nullable=True, index=True)
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
    media = relationship(
        "Media",
        secondary=article_media,
        backref=backref("media", lazy="dynamic"),
        lazy="dynamic",
    )
    misc = relationship(
        "Misc",
        secondary=article_misc,
        backref=backref("misc", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return "<Article(id='{id}', title='{title}')>".format(
            id=self.id, title=self.title
        )
