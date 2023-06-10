import typing as t
from os import environ

import factory
from factory import Faker

from . import models
from .models import Article, Author, Image, Media, Misc, Tag


class AuthorFactory(factory.Factory):
    class Meta:
        model: t.Type[Author] = models.Author

    name: Faker = factory.Faker("name")


class ImageFactory(factory.Factory):
    class Meta:
        model: t.Type[Image] = models.Image

    path: Faker = factory.Faker("file_path", depth=3, extension="jpg")
    description: Faker = factory.Faker("sentence", nb_words=12, variable_nb_words=True)


class TagFactory(factory.Factory):
    class Meta:
        model: t.Type[Tag] = models.Tag

    name: Faker = factory.Faker("sentence", nb_words=3, variable_nb_words=True)


class MiscFactory(factory.Factory):
    class Meta:
        model: t.Type[Misc] = models.Misc

    big_integer_field: Faker = factory.Faker("pyint", max_value=10**9)
    blob_field: Faker = factory.Faker("binary", length=1024 * 10)
    boolean_field: Faker = factory.Faker("boolean")
    char_field: Faker = factory.Faker("text", max_nb_chars=255)
    date_field: Faker = factory.Faker("date_this_decade")
    date_time_field: Faker = factory.Faker("date_time_this_century")
    decimal_field: Faker = factory.Faker("pydecimal", left_digits=8, right_digits=2)
    float_field: Faker = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    integer_field: Faker = factory.Faker("pyint", min_value=-(2**31), max_value=2**31 - 1)
    if environ.get("LEGACY_DB", "0") == "0":
        json_field = factory.Faker(
            "pydict",
            nb_elements=10,
            variable_nb_elements=True,
            value_types=["str", "int", "float", "boolean", "date_time"],
        )
    numeric_field: Faker = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    real_field: Faker = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    small_integer_field: Faker = factory.Faker("pyint", min_value=-(2**15), max_value=2**15 - 1)
    string_field: Faker = factory.Faker("text", max_nb_chars=255)
    text_field: Faker = factory.Faker("text", max_nb_chars=1024)
    time_field: Faker = factory.Faker("time_object")
    varchar_field: Faker = factory.Faker("text", max_nb_chars=255)
    timestamp_field: Faker = factory.Faker("date_time_this_century")
    my_type_field: Faker = factory.Faker("text", max_nb_chars=255)


class ArticleFactory(factory.Factory):
    class Meta:
        model: t.Type[Article] = models.Article

    hash: Faker = factory.Faker("md5")
    title: Faker = factory.Faker("sentence", nb_words=6)
    slug: Faker = factory.Faker("slug")
    content: Faker = factory.Faker("text", max_nb_chars=1024)
    status: Faker = factory.Faker("pystr", max_chars=1)
    published: Faker = factory.Faker("date_between", start_date="-1y", end_date="-1d")

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of authors were passed in, use them
            for author in extracted:
                self.authors.add(author)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of authors were passed in, use them
            for tag in extracted:
                self.tags.add(tag)

    @factory.post_generation
    def images(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of authors were passed in, use them
            for image in extracted:
                self.images.add(image)

    @factory.post_generation
    def misc(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of authors were passed in, use them
            for misc in extracted:
                self.misc.add(misc)


class MediaFactory(factory.Factory):
    class Meta:
        model: t.Type[Media] = models.Media

    id: Faker = factory.Faker("sha256", raw_output=False)
    title: Faker = factory.Faker("sentence", nb_words=6)
    description: Faker = factory.Faker("sentence", nb_words=12, variable_nb_words=True)
