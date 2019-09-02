from datetime import datetime, timedelta
from decimal import Decimal

import simplejson as json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists

from .models import Base


class Database:
    engine = None
    Session = None

    def __init__(self, database_uri):
        self.Session = sessionmaker()
        self.engine = create_engine(
            database_uri, json_serializer=self.dumps, json_deserializer=json.loads
        )
        if not database_exists(database_uri):
            self._create_db_tables()
        self.Session.configure(bind=self.engine)

    def _create_db_tables(self):
        Base.metadata.create_all(self.engine)

    @classmethod
    def dumps(cls, data):
        return json.dumps(data, default=cls.json_serializer)

    @staticmethod
    def json_serializer(data):
        if isinstance(data, datetime):
            return data.isoformat()
        if isinstance(data, Decimal):
            return str(data)
        if isinstance(data, timedelta):
            hours, remainder = divmod(data.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
