import typing as t
from datetime import date, datetime, time
from decimal import Decimal
from os import environ

import sqlalchemy.types as types
from sqlalchemy import (
    BLOB,
    CHAR,
    JSON,
    REAL,
    TIMESTAMP,
    VARCHAR,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    Time,
)
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.orm import backref, declarative_base, relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.sql.functions import current_timestamp


class SQLiteNumeric(types.TypeDecorator):
    impl: t.Type[String] = types.String

    def load_dialect_impl(self, dialect: SQLiteDialect) -> t.Any:
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value: t.Any, dialect: SQLiteDialect) -> str:
        return str(value)

    def process_result_value(self, value: t.Any, dialect: SQLiteDialect) -> Decimal:
        return Decimal(value)


class MyCustomType(types.TypeDecorator):
    impl: t.Type[String] = types.String

    def load_dialect_impl(self, dialect: SQLiteDialect) -> t.Any:
        return dialect.type_descriptor(types.VARCHAR(self.length))

    def process_bind_param(self, value: t.Any, dialect: SQLiteDialect) -> str:
        return str(value)

    def process_result_value(self, value: t.Any, dialect: SQLiteDialect) -> str:
        return str(value)


Base: DeclarativeMeta = declarative_base()


class Author(Base):
    __tablename__ = "authors"
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(128), nullable=False, index=True)

    def __repr__(self):
        return "<Author(id='{id}', name='{name}')>".format(id=self.id, name=self.name)


article_authors: Table = Table(
    "article_authors",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)


class Image(Base):
    __tablename__ = "images"
    id: int = Column(Integer, primary_key=True)
    path: str = Column(String(255), index=True)
    description: str = Column(String(255), nullable=True)

    def __repr__(self):
        return "<Image(id='{id}', path='{path}')>".format(id=self.id, path=self.path)


article_images: Table = Table(
    "article_images",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(128), nullable=False, index=True)

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
    id: int = Column(Integer, primary_key=True)
    big_integer_field: int = Column(BigInteger, default=0)
    blob_field: bytes = Column(BLOB, nullable=True, index=True)
    boolean_field: bool = Column(Boolean, default=False)
    char_field: str = Column(CHAR(255), nullable=True)
    date_field: date = Column(Date, nullable=True)
    date_time_field: datetime = Column(DateTime, nullable=True)
    decimal_field: Decimal = Column(SQLiteNumeric(10, 2), nullable=True)
    float_field: Decimal = Column(SQLiteNumeric(12, 4), default=0)
    integer_field: int = Column(Integer, default=0)
    if environ.get("LEGACY_DB", "0") == "0":
        json_field: t.Dict[str, t.Any] = Column(JSON, nullable=True)
    numeric_field: Decimal = Column(SQLiteNumeric(12, 4), default=0)
    real_field: float = Column(REAL(12, 4), default=0)
    small_integer_field: int = Column(SmallInteger, default=0)
    string_field: str = Column(String(255), nullable=True)
    text_field: str = Column(Text, nullable=True)
    time_field: time = Column(Time, nullable=True)
    varchar_field: str = Column(VARCHAR(255), nullable=True)
    timestamp_field: datetime = Column(TIMESTAMP, default=current_timestamp())
    my_type_field: t.Any = Column(MyCustomType(255), nullable=True)


article_misc: Table = Table(
    "article_misc",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("misc_id", Integer, ForeignKey("misc.id"), primary_key=True),
)


class Media(Base):
    __tablename__ = "media"
    id: str = Column(CHAR(64), primary_key=True)
    title: str = Column(String(255), index=True)
    description: str = Column(String(255), nullable=True)

    def __repr__(self):
        return "<Media(id='{id}', title='{title}')>".format(id=self.id, title=self.title)


article_media = Table(
    "article_media",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("media_id", CHAR(64), ForeignKey("media.id"), primary_key=True),
)


class Article(Base):
    __tablename__ = "articles"
    id: int = Column(Integer, primary_key=True)
    hash: str = Column(String(32), unique=True)
    slug: str = Column(String(255), index=True)
    title: str = Column(String(255), index=True)
    content: str = Column(Text, nullable=True, index=True)
    status: str = Column(CHAR(1), index=True)
    published: datetime = Column(DateTime, nullable=True)
    # relationships
    authors: t.List[Author] = relationship(
        "Author",
        secondary=article_authors,
        backref=backref("authors", lazy="dynamic"),
        lazy="dynamic",
    )
    tags: t.List[Tag] = relationship(
        "Tag",
        secondary=article_tags,
        backref=backref("tags", lazy="dynamic"),
        lazy="dynamic",
    )
    images: t.List[Image] = relationship(
        "Image",
        secondary=article_images,
        backref=backref("images", lazy="dynamic"),
        lazy="dynamic",
    )
    media: t.List[Media] = relationship(
        "Media",
        secondary=article_media,
        backref=backref("media", lazy="dynamic"),
        lazy="dynamic",
    )
    misc: t.List[Misc] = relationship(
        "Misc",
        secondary=article_misc,
        backref=backref("misc", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return "<Article(id='{id}', title='{title}')>".format(id=self.id, title=self.title)
