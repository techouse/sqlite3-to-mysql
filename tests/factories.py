from os import environ

import factory

from . import models


class AuthorFactory(factory.Factory):
    class Meta:
        model = models.Author

    name = factory.Faker("name")


class ImageFactory(factory.Factory):
    class Meta:
        model = models.Image

    path = factory.Faker("file_path", depth=3, extension="jpg")
    description = factory.Faker("sentence", nb_words=12, variable_nb_words=True)


class TagFactory(factory.Factory):
    class Meta:
        model = models.Tag

    name = factory.Faker("sentence", nb_words=3, variable_nb_words=True)


class MiscFactory(factory.Factory):
    class Meta:
        model = models.Misc

    big_integer_field = factory.Faker("pyint", max_value=10 ** 9)
    blob_field = factory.Faker("binary", length=1024 * 10)
    boolean_field = factory.Faker("boolean")
    char_field = factory.Faker("text", max_nb_chars=255)
    date_field = factory.Faker("date_this_decade")
    date_time_field = factory.Faker("date_time_this_century")
    decimal_field = factory.Faker("pydecimal", left_digits=8, right_digits=2)
    float_field = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    integer_field = factory.Faker("pyint", min_value=-(2 ** 31), max_value=2 ** 31 - 1)
    if environ.get("LEGACY_DB", "0") == "0":
        json_field = factory.Faker("pydict")
    numeric_field = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    real_field = factory.Faker("pyfloat", left_digits=8, right_digits=4)
    small_integer_field = factory.Faker(
        "pyint", min_value=-(2 ** 15), max_value=2 ** 15 - 1
    )
    string_field = factory.Faker("text", max_nb_chars=255)
    text_field = factory.Faker("text", max_nb_chars=1024)
    time_field = factory.Faker("time_object")
    varchar_field = factory.Faker("text", max_nb_chars=255)
    timestamp_field = factory.Faker("date_time_this_century")
    my_type_field = factory.Faker("text", max_nb_chars=255)


class ArticleFactory(factory.Factory):
    class Meta:
        model = models.Article

    hash = factory.Faker("md5")
    title = factory.Faker("sentence", nb_words=6)
    slug = factory.Faker("slug")
    content = factory.Faker("text", max_nb_chars=1024)
    status = factory.Faker("pystr", max_chars=1)
    published = factory.Faker("date_between", start_date="-1y", end_date="-1d")

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
        model = models.Media

    id = factory.Faker("sha256", raw_output=False)
    title = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("sentence", nb_words=12, variable_nb_words=True)
