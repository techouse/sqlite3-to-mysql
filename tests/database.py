from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists

from .models import Base


class Database:
    engine = None
    Session = None

    def __init__(self, database_uri):
        self.Session = sessionmaker()
        self.engine = create_engine(database_uri)
        if not database_exists(database_uri):
            self._create_db_tables()
        self.Session.configure(bind=self.engine)

    def _create_db_tables(self):
        Base.metadata.create_all(self.engine)
