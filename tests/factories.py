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


class ArticleFactory(factory.Factory):
    class Meta:
        model = models.Article

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
