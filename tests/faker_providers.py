import datetime
from typing import Optional

from faker.providers import BaseProvider, date_time
from faker.typing import DateParseType


class DateTimeProviders(BaseProvider):
    def time_object_without_microseconds(self, end_datetime: Optional[DateParseType] = None) -> datetime.time:
        return date_time.Provider(self.generator).time_object(end_datetime).replace(microsecond=0)

    def date_time_this_century_without_microseconds(
        self,
        before_now: bool = True,
        after_now: bool = False,
        tzinfo: Optional[datetime.tzinfo] = None,
    ) -> datetime.datetime:
        return (
            date_time.Provider(self.generator)
            .date_time_this_century(before_now, after_now, tzinfo)
            .replace(microsecond=0)
        )
