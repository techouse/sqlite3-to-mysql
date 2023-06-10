import typing as t
from datetime import date, datetime, time
from decimal import Decimal
from os import environ

import sqlalchemy.types as types
from sqlalchemy import (
    BLOB,
    CHAR,
    DECIMAL,
    JSON,
    REAL,
    TIMESTAMP,
    VARCHAR,
    BigInteger,
    Column,
    Dialect,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, backref, mapped_column, relationship
from sqlalchemy.sql.functions import current_timestamp


class MyCustomType(types.TypeDecorator):
    impl: t.Type[String] = types.String

    def load_dialect_impl(self, dialect: Dialect) -> t.Any:
        return dialect.type_descriptor(types.VARCHAR(self.length))

    def process_bind_param(self, value: t.Any, dialect: Dialect) -> str:
        return str(value)

    def process_result_value(self, value: t.Any, dialect: Dialect) -> str:
        return str(value)


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    def __repr__(self):
        return f"<Author(id='{self.id}', name='{self.name}')>"


article_authors: Table = Table(
    "article_authors",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)


class Image(Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"<Image(id='{self.id}', path='{self.path}')>"


article_images: Table = Table(
    "article_images",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    def __repr__(self):
        return f"<Tag(id='{self.id}', name='{self.name}')>"


article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Misc(Base):
    """This model contains all possible MySQL types"""

    __tablename__ = "misc"
    id: Mapped[int] = mapped_column(primary_key=True)
    big_integer_field: Mapped[int] = mapped_column(BigInteger, default=0)
    blob_field: Mapped[bytes] = mapped_column(BLOB, nullable=True, index=True)
    boolean_field: Mapped[bool] = mapped_column(default=False)
    char_field: Mapped[str] = mapped_column(CHAR(255), nullable=True)
    date_field: Mapped[date] = mapped_column(nullable=True)
    date_time_field: Mapped[datetime] = mapped_column(nullable=True)
    decimal_field: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True)
    float_field: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0)
    integer_field: Mapped[int] = mapped_column(default=0)
    if environ.get("LEGACY_DB", "0") == "0":
        json_field: Mapped[t.Mapping[str, t.Any]] = mapped_column(JSON, nullable=True)
    numeric_field: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0)
    real_field: Mapped[float] = mapped_column(REAL(12), default=0)
    small_integer_field: Mapped[int] = mapped_column(SmallInteger, default=0)
    string_field: Mapped[str] = mapped_column(String(255), nullable=True)
    text_field: Mapped[str] = mapped_column(Text, nullable=True)
    time_field: Mapped[time] = mapped_column(nullable=True)
    varchar_field: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    timestamp_field: Mapped[datetime] = mapped_column(TIMESTAMP, default=current_timestamp())
    my_type_field: Mapped[t.Any] = mapped_column(MyCustomType(255), nullable=True)


article_misc: Table = Table(
    "article_misc",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("misc_id", Integer, ForeignKey("misc.id"), primary_key=True),
)


class Media(Base):
    __tablename__ = "media"
    id: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"<Media(id='{self.id}', title='{self.title}')>"


article_media = Table(
    "article_media",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("media_id", CHAR(64), ForeignKey("media.id"), primary_key=True),
)


class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    hash: Mapped[str] = mapped_column(String(32), unique=True)
    slug: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(Text, nullable=True, index=True)
    status: Mapped[str] = mapped_column(CHAR(1), index=True)
    published: Mapped[datetime] = mapped_column(nullable=True)
    # relationships
    authors: Mapped[t.List[Author]] = relationship(
        "Author",
        secondary=article_authors,
        backref=backref("authors", lazy="dynamic"),
        lazy="dynamic",
    )
    tags: Mapped[t.List[Tag]] = relationship(
        "Tag",
        secondary=article_tags,
        backref=backref("tags", lazy="dynamic"),
        lazy="dynamic",
    )
    images: Mapped[t.List[Image]] = relationship(
        "Image",
        secondary=article_images,
        backref=backref("images", lazy="dynamic"),
        lazy="dynamic",
    )
    media: Mapped[t.List[Media]] = relationship(
        "Media",
        secondary=article_media,
        backref=backref("media", lazy="dynamic"),
        lazy="dynamic",
    )
    misc: Mapped[t.List[Misc]] = relationship(
        "Misc",
        secondary=article_misc,
        backref=backref("misc", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Article(id='{self.id}', title='{self.title}')>"
