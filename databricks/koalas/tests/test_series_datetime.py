#
# Copyright (C) 2019 Databricks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import datetime
import unittest

import numpy as np
import pandas as pd

from databricks import koalas as ks
from databricks.koalas.testing.utils import ReusedSQLTestCase, SQLTestUtils


class SeriesDateTimeTest(ReusedSQLTestCase, SQLTestUtils):
    @property
    def pdf1(self):
        date1 = pd.Series(pd.date_range("2012-1-1 12:45:31", periods=3, freq="M"))
        date2 = pd.Series(pd.date_range("2013-3-11 21:45:00", periods=3, freq="W"))
        return pd.DataFrame(dict(start_date=date1, end_date=date2))

    @property
    def pd_start_date(self):
        return self.pdf1["start_date"]

    @property
    def ks_start_date(self):
        return ks.from_pandas(self.pd_start_date)

    def check_func(self, func):
        self.assert_eq(func(self.ks_start_date), func(self.pd_start_date))

    def test_timestamp_subtraction(self):
        pdf = self.pdf1
        kdf = ks.from_pandas(pdf)

        # Those fail in certain OSs presumably due to different
        # timezone behaviours inherited from C library.

        actual = (kdf["end_date"] - kdf["start_date"] - 1).to_pandas()
        expected = (pdf["end_date"] - pdf["start_date"]) // np.timedelta64(1, "s") - 1
        # self.assert_eq(actual, expected)

        actual = (kdf["end_date"] - pd.Timestamp("2012-1-1 12:45:31") - 1).to_pandas()
        expected = (pdf["end_date"] - pd.Timestamp("2012-1-1 12:45:31")) // np.timedelta64(
            1, "s"
        ) - 1
        # self.assert_eq(actual, expected)

        actual = (pd.Timestamp("2013-3-11 21:45:00") - kdf["start_date"] - 1).to_pandas()
        expected = (pd.Timestamp("2013-3-11 21:45:00") - pdf["start_date"]) // np.timedelta64(
            1, "s"
        ) - 1
        # self.assert_eq(actual, expected)

        kdf = ks.DataFrame(
            {"a": pd.date_range("2016-12-31", "2017-01-08", freq="D"), "b": pd.Series(range(9))}
        )
        expected_error_message = "datetime subtraction can only be applied to datetime series."
        with self.assertRaisesRegex(TypeError, expected_error_message):
            kdf["a"] - kdf["b"]
        with self.assertRaisesRegex(TypeError, expected_error_message):
            kdf["a"] - 1
        with self.assertRaisesRegex(TypeError, expected_error_message):
            1 - kdf["a"]

    def test_arithmetic_op_exceptions(self):
        kser = self.ks_start_date
        py_datetime = self.pd_start_date.dt.to_pydatetime()
        datetime_index = ks.Index(self.pd_start_date)

        for other in [1, 0.1, kser, datetime_index, py_datetime]:
            expected_err_msg = "addition can not be applied to date times."
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: kser + other)
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: other + kser)

            expected_err_msg = "multiplication can not be applied to date times."
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: kser * other)
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: other * kser)

            expected_err_msg = "division can not be applied to date times."
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: kser / other)
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: other / kser)
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: kser // other)
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: other // kser)

            expected_err_msg = "modulo can not be applied to date times."
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: kser % other)
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: other % kser)

        expected_err_msg = "datetime subtraction can only be applied to datetime series."

        for other in [1, 0.1]:
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: kser - other)
            self.assertRaisesRegex(TypeError, expected_err_msg, lambda: other - kser)

        self.assertRaisesRegex(TypeError, expected_err_msg, lambda: kser - other)
        self.assertRaises(NotImplementedError, lambda: py_datetime - kser)

    def test_date_subtraction(self):
        pdf = self.pdf1
        kdf = ks.from_pandas(pdf)

        self.assert_eq(
            kdf["end_date"].dt.date - kdf["start_date"].dt.date,
            (pdf["end_date"].dt.date - pdf["start_date"].dt.date).dt.days,
        )

        self.assert_eq(
            kdf["end_date"].dt.date - datetime.date(2012, 1, 1),
            (pdf["end_date"].dt.date - datetime.date(2012, 1, 1)).dt.days,
        )

        self.assert_eq(
            datetime.date(2013, 3, 11) - kdf["start_date"].dt.date,
            (datetime.date(2013, 3, 11) - pdf["start_date"].dt.date).dt.days,
        )

        kdf = ks.DataFrame(
            {"a": pd.date_range("2016-12-31", "2017-01-08", freq="D"), "b": pd.Series(range(9))}
        )
        expected_error_message = "date subtraction can only be applied to date series."
        with self.assertRaisesRegex(TypeError, expected_error_message):
            kdf["a"].dt.date - kdf["b"]
        with self.assertRaisesRegex(TypeError, expected_error_message):
            kdf["a"].dt.date - 1
        with self.assertRaisesRegex(TypeError, expected_error_message):
            1 - kdf["a"].dt.date

    @unittest.skip(
        "It fails in certain OSs presumably due to different "
        "timezone behaviours inherited from C library."
    )
    def test_div(self):
        pdf = self.pdf1
        kdf = ks.from_pandas(pdf)
        for u in "D", "s", "ms":
            duration = np.timedelta64(1, u)
            self.assert_eq(
                (kdf["end_date"] - kdf["start_date"]) / duration,
                (pdf["end_date"] - pdf["start_date"]) / duration,
            )

    @unittest.skip("It is currently failed probably for the same reason in 'test_subtraction'")
    def test_date(self):
        self.check_func(lambda x: x.dt.date)

    def test_time(self):
        with self.assertRaises(NotImplementedError):
            self.check_func(lambda x: x.dt.time)

    def test_timetz(self):
        with self.assertRaises(NotImplementedError):
            self.check_func(lambda x: x.dt.timetz)

    def test_year(self):
        self.check_func(lambda x: x.dt.year)

    def test_month(self):
        self.check_func(lambda x: x.dt.month)

    def test_day(self):
        self.check_func(lambda x: x.dt.day)

    def test_hour(self):
        self.check_func(lambda x: x.dt.hour)

    def test_minute(self):
        self.check_func(lambda x: x.dt.minute)

    def test_second(self):
        self.check_func(lambda x: x.dt.second)

    def test_microsecond(self):
        self.check_func(lambda x: x.dt.microsecond)

    def test_nanosecond(self):
        with self.assertRaises(NotImplementedError):
            self.check_func(lambda x: x.dt.nanosecond)

    def test_week(self):
        self.check_func(lambda x: x.dt.week)

    def test_weekofyear(self):
        self.check_func(lambda x: x.dt.weekofyear)

    def test_dayofweek(self):
        self.check_func(lambda x: x.dt.dayofweek)

    def test_weekday(self):
        self.check_func(lambda x: x.dt.weekday)

    def test_dayofyear(self):
        self.check_func(lambda x: x.dt.dayofyear)

    def test_quarter(self):
        self.check_func(lambda x: x.dt.dayofyear)

    def test_is_month_start(self):
        self.check_func(lambda x: x.dt.is_month_start)

    def test_is_month_end(self):
        self.check_func(lambda x: x.dt.is_month_end)

    def test_is_quarter_start(self):
        self.check_func(lambda x: x.dt.is_quarter_start)

    def test_is_quarter_end(self):
        self.check_func(lambda x: x.dt.is_quarter_end)

    def test_is_year_start(self):
        self.check_func(lambda x: x.dt.is_year_start)

    def test_is_year_end(self):
        self.check_func(lambda x: x.dt.is_year_end)

    def test_is_leap_year(self):
        self.check_func(lambda x: x.dt.is_leap_year)

    def test_daysinmonth(self):
        self.check_func(lambda x: x.dt.daysinmonth)

    def test_days_in_month(self):
        self.check_func(lambda x: x.dt.days_in_month)

    @unittest.expectedFailure
    def test_tz_localize(self):
        self.check_func(lambda x: x.dt.tz_localize("America/New_York"))

    @unittest.expectedFailure
    def test_tz_convert(self):
        self.check_func(lambda x: x.dt.tz_convert("America/New_York"))

    def test_normalize(self):
        self.check_func(lambda x: x.dt.normalize())

    def test_strftime(self):
        self.check_func(lambda x: x.dt.strftime("%Y-%m-%d"))

    def test_round(self):
        self.check_func(lambda x: x.dt.round(freq="min"))
        self.check_func(lambda x: x.dt.round(freq="H"))

    def test_floor(self):
        self.check_func(lambda x: x.dt.floor(freq="min"))
        self.check_func(lambda x: x.dt.floor(freq="H"))

    def test_ceil(self):
        self.check_func(lambda x: x.dt.floor(freq="min"))
        self.check_func(lambda x: x.dt.floor(freq="H"))

    def test_month_name(self):
        self.check_func(lambda x: x.dt.month_name())
        self.check_func(lambda x: x.dt.month_name(locale="en_US.UTF-8"))

    def test_day_name(self):
        self.check_func(lambda x: x.dt.day_name())
        self.check_func(lambda x: x.dt.day_name(locale="en_US.UTF-8"))

    def test_unsupported_type(self):
        self.assertRaisesRegex(
            ValueError, "Cannot call DatetimeMethods on type LongType", lambda: ks.Series([0]).dt
        )
