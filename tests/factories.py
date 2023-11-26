import typing as t
from os import environ

import factory

from . import faker_providers, models


factory.Faker.add_provider(faker_providers.DateTimeProviders)


class AuthorFactory(factory.Factory):
    class Meta:
        model: t.Type[models.Author] = models.Author

    name: factory.Faker = factory.Faker("name")


class ImageFactory(factory.Factory):
    class Meta:
        model: t.Type[models.Image] = models.Image

    path: factory.Faker = factory.Faker("file_path", depth=3, extension="jpg")
    description: factory.Faker = factory.Faker("sentence", nb_words=12, variable_nb_words=True)


class TagFactory(factory.Factory):
    class Meta:
        model: t.Type[models.Tag] = models.Tag

    name: factory.Faker = factory.Faker("sentence", nb_words=3, variable_nb_words=True)


class MiscFactory(factory.Factory):
    class Meta:
        model: t.Type[models.Misc] = models.Misc

    big_integer_field: factory.Faker = factory.Faker("pyint", max_value=10**9)
    blob_field: factory.Faker = factory.Faker("binary", length=1024 * 10)
    boolean_field: factory.Faker = factory.Faker("boolean")
    char_field: factory.Faker = factory.Faker("text", max_nb_chars=255)
    date_field: factory.Faker = factory.Faker("date_this_decade")
    date_time_field: factory.Faker = factory.Faker("date_time_this_century_without_microseconds")
    decimal_field: factory.Faker = factory.Faker("pydecimal", left_digits=8, right_digits=2)
    float_field: factory.Faker = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    integer_field: factory.Faker = factory.Faker("pyint", min_value=-(2**31), max_value=2**31 - 1)
    if environ.get("LEGACY_DB", "0") == "0":
        json_field = factory.Faker(
            "pydict",
            nb_elements=10,
            variable_nb_elements=True,
            value_types=["str", "int", "float", "boolean", "date_time"],
        )
    numeric_field: factory.Faker = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    real_field: factory.Faker = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    small_integer_field: factory.Faker = factory.Faker("pyint", min_value=-(2**15), max_value=2**15 - 1)
    string_field: factory.Faker = factory.Faker("text", max_nb_chars=255)
    text_field: factory.Faker = factory.Faker("text", max_nb_chars=1024)
    time_field: factory.Faker = factory.Faker("time_object_without_microseconds")
    varchar_field: factory.Faker = factory.Faker("text", max_nb_chars=255)
    timestamp_field: factory.Faker = factory.Faker("date_time_this_century_without_microseconds")
    my_type_field: factory.Faker = factory.Faker("text", max_nb_chars=255)


class ArticleFactory(factory.Factory):
    class Meta:
        model: t.Type[models.Article] = models.Article

    hash: factory.Faker = factory.Faker("md5")
    title: factory.Faker = factory.Faker("sentence", nb_words=6)
    slug: factory.Faker = factory.Faker("slug")
    content: factory.Faker = factory.Faker("text", max_nb_chars=1024)
    status: factory.Faker = factory.Faker("pystr", max_chars=1)
    published: factory.Faker = factory.Faker("date_between", start_date="-1y", end_date="-1d")

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
        model: t.Type[models.Media] = models.Media

    id: factory.Faker = factory.Faker("sha256", raw_output=False)
    title: factory.Faker = factory.Faker("sentence", nb_words=6)
    description: factory.Faker = factory.Faker("sentence", nb_words=12, variable_nb_words=True)
