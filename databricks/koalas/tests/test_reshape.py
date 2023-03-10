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
from decimal import Decimal
from distutils.version import LooseVersion

import numpy as np
import pandas as pd
import pyspark

from databricks import koalas as ks
from databricks.koalas.testing.utils import ReusedSQLTestCase, SPARK_CONF_ARROW_ENABLED
from databricks.koalas.utils import name_like_string


class ReshapeTest(ReusedSQLTestCase):
    def test_get_dummies(self):
        for pdf_or_ps in [
            pd.Series([1, 1, 1, 2, 2, 1, 3, 4]),
            # pd.Series([1, 1, 1, 2, 2, 1, 3, 4], dtype='category'),
            # pd.Series(pd.Categorical([1, 1, 1, 2, 2, 1, 3, 4],
            #                          categories=[4, 3, 2, 1])),
            pd.DataFrame(
                {
                    "a": [1, 2, 3, 4, 4, 3, 2, 1],
                    # 'b': pd.Categorical(list('abcdabcd')),
                    "b": list("abcdabcd"),
                }
            ),
            pd.DataFrame({10: [1, 2, 3, 4, 4, 3, 2, 1], 20: list("abcdabcd")}),
        ]:
            kdf_or_kser = ks.from_pandas(pdf_or_ps)

            self.assert_eq(ks.get_dummies(kdf_or_kser), pd.get_dummies(pdf_or_ps, dtype=np.int8))

        kser = ks.Series([1, 1, 1, 2, 2, 1, 3, 4])
        with self.assertRaisesRegex(
            NotImplementedError, "get_dummies currently does not support sparse"
        ):
            ks.get_dummies(kser, sparse=True)

    def test_get_dummies_object(self):
        pdf = pd.DataFrame(
            {
                "a": [1, 2, 3, 4, 4, 3, 2, 1],
                # 'a': pd.Categorical([1, 2, 3, 4, 4, 3, 2, 1]),
                "b": list("abcdabcd"),
                # 'c': pd.Categorical(list('abcdabcd')),
                "c": list("abcdabcd"),
            }
        )
        kdf = ks.from_pandas(pdf)

        # Explicitly exclude object columns
        self.assert_eq(
            ks.get_dummies(kdf, columns=["a", "c"]),
            pd.get_dummies(pdf, columns=["a", "c"], dtype=np.int8),
        )

        self.assert_eq(ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8))
        self.assert_eq(ks.get_dummies(kdf.b), pd.get_dummies(pdf.b, dtype=np.int8))
        self.assert_eq(
            ks.get_dummies(kdf, columns=["b"]), pd.get_dummies(pdf, columns=["b"], dtype=np.int8)
        )

        self.assertRaises(KeyError, lambda: ks.get_dummies(kdf, columns=("a", "c")))
        self.assertRaises(TypeError, lambda: ks.get_dummies(kdf, columns="b"))

        # non-string names
        pdf = pd.DataFrame(
            {10: [1, 2, 3, 4, 4, 3, 2, 1], 20: list("abcdabcd"), 30: list("abcdabcd")}
        )
        kdf = ks.from_pandas(pdf)

        self.assert_eq(
            ks.get_dummies(kdf, columns=[10, 30]),
            pd.get_dummies(pdf, columns=[10, 30], dtype=np.int8),
        )

        self.assertRaises(TypeError, lambda: ks.get_dummies(kdf, columns=10))

    def test_get_dummies_date_datetime(self):
        pdf = pd.DataFrame(
            {
                "d": [
                    datetime.date(2019, 1, 1),
                    datetime.date(2019, 1, 2),
                    datetime.date(2019, 1, 1),
                ],
                "dt": [
                    datetime.datetime(2019, 1, 1, 0, 0, 0),
                    datetime.datetime(2019, 1, 1, 0, 0, 1),
                    datetime.datetime(2019, 1, 1, 0, 0, 0),
                ],
            }
        )
        kdf = ks.from_pandas(pdf)

        if LooseVersion(pyspark.__version__) >= LooseVersion("2.4"):
            self.assert_eq(ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8))
            self.assert_eq(ks.get_dummies(kdf.d), pd.get_dummies(pdf.d, dtype=np.int8))
            self.assert_eq(ks.get_dummies(kdf.dt), pd.get_dummies(pdf.dt, dtype=np.int8))
        else:
            with self.sql_conf({SPARK_CONF_ARROW_ENABLED: False}):
                self.assert_eq(ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8))
                self.assert_eq(ks.get_dummies(kdf.d), pd.get_dummies(pdf.d, dtype=np.int8))
                self.assert_eq(ks.get_dummies(kdf.dt), pd.get_dummies(pdf.dt, dtype=np.int8))

    def test_get_dummies_boolean(self):
        pdf = pd.DataFrame({"b": [True, False, True]})
        kdf = ks.from_pandas(pdf)

        if LooseVersion(pyspark.__version__) >= LooseVersion("2.4"):
            self.assert_eq(ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8))
            self.assert_eq(ks.get_dummies(kdf.b), pd.get_dummies(pdf.b, dtype=np.int8))
        else:
            with self.sql_conf({SPARK_CONF_ARROW_ENABLED: False}):
                self.assert_eq(ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8))
                self.assert_eq(ks.get_dummies(kdf.b), pd.get_dummies(pdf.b, dtype=np.int8))

    def test_get_dummies_decimal(self):
        pdf = pd.DataFrame({"d": [Decimal(1.0), Decimal(2.0), Decimal(1)]})
        kdf = ks.from_pandas(pdf)

        if LooseVersion(pyspark.__version__) >= LooseVersion("2.4"):
            self.assert_eq(ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8))
            self.assert_eq(ks.get_dummies(kdf.d), pd.get_dummies(pdf.d, dtype=np.int8), almost=True)
        else:
            with self.sql_conf({SPARK_CONF_ARROW_ENABLED: False}):
                self.assert_eq(ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8))
                self.assert_eq(
                    ks.get_dummies(kdf.d), pd.get_dummies(pdf.d, dtype=np.int8), almost=True
                )

    def test_get_dummies_kwargs(self):
        # pser = pd.Series([1, 1, 1, 2, 2, 1, 3, 4], dtype='category')
        pser = pd.Series([1, 1, 1, 2, 2, 1, 3, 4])
        kser = ks.from_pandas(pser)
        self.assert_eq(
            ks.get_dummies(kser, prefix="X", prefix_sep="-"),
            pd.get_dummies(pser, prefix="X", prefix_sep="-", dtype=np.int8),
        )

        self.assert_eq(
            ks.get_dummies(kser, drop_first=True),
            pd.get_dummies(pser, drop_first=True, dtype=np.int8),
        )

        # nan
        # pser = pd.Series([1, 1, 1, 2, np.nan, 3, np.nan, 5], dtype='category')
        pser = pd.Series([1, 1, 1, 2, np.nan, 3, np.nan, 5])
        kser = ks.from_pandas(pser)
        self.assert_eq(ks.get_dummies(kser), pd.get_dummies(pser, dtype=np.int8), almost=True)

        # dummy_na
        self.assert_eq(
            ks.get_dummies(kser, dummy_na=True), pd.get_dummies(pser, dummy_na=True, dtype=np.int8)
        )

    def test_get_dummies_prefix(self):
        pdf = pd.DataFrame({"A": ["a", "b", "a"], "B": ["b", "a", "c"], "D": [0, 0, 1]})
        kdf = ks.from_pandas(pdf)

        self.assert_eq(
            ks.get_dummies(kdf, prefix=["foo", "bar"]),
            pd.get_dummies(pdf, prefix=["foo", "bar"], dtype=np.int8),
        )

        self.assert_eq(
            ks.get_dummies(kdf, prefix=["foo"], columns=["B"]),
            pd.get_dummies(pdf, prefix=["foo"], columns=["B"], dtype=np.int8),
        )

        self.assert_eq(
            ks.get_dummies(kdf, prefix={"A": "foo", "B": "bar"}),
            pd.get_dummies(pdf, prefix={"A": "foo", "B": "bar"}, dtype=np.int8),
        )

        self.assert_eq(
            ks.get_dummies(kdf, prefix={"B": "foo", "A": "bar"}),
            pd.get_dummies(pdf, prefix={"B": "foo", "A": "bar"}, dtype=np.int8),
        )

        self.assert_eq(
            ks.get_dummies(kdf, prefix={"A": "foo", "B": "bar"}, columns=["A", "B"]),
            pd.get_dummies(pdf, prefix={"A": "foo", "B": "bar"}, columns=["A", "B"], dtype=np.int8),
        )

        with self.assertRaisesRegex(NotImplementedError, "string types"):
            ks.get_dummies(kdf, prefix="foo")
        with self.assertRaisesRegex(ValueError, "Length of 'prefix' \\(1\\) .* \\(2\\)"):
            ks.get_dummies(kdf, prefix=["foo"])
        with self.assertRaisesRegex(ValueError, "Length of 'prefix' \\(2\\) .* \\(1\\)"):
            ks.get_dummies(kdf, prefix=["foo", "bar"], columns=["B"])

        pser = pd.Series([1, 1, 1, 2, 2, 1, 3, 4], name="A")
        kser = ks.from_pandas(pser)

        self.assert_eq(
            ks.get_dummies(kser, prefix="foo"), pd.get_dummies(pser, prefix="foo", dtype=np.int8)
        )

        # columns are ignored.
        self.assert_eq(
            ks.get_dummies(kser, prefix=["foo"], columns=["B"]),
            pd.get_dummies(pser, prefix=["foo"], columns=["B"], dtype=np.int8),
        )

    def test_get_dummies_dtype(self):
        pdf = pd.DataFrame(
            {
                # "A": pd.Categorical(['a', 'b', 'a'], categories=['a', 'b', 'c']),
                "A": ["a", "b", "a"],
                "B": [0, 0, 1],
            }
        )
        kdf = ks.from_pandas(pdf)

        if LooseVersion("0.23.0") <= LooseVersion(pd.__version__):
            exp = pd.get_dummies(pdf, dtype="float64")
        else:
            exp = pd.get_dummies(pdf)
            exp = exp.astype({"A_a": "float64", "A_b": "float64"})
        res = ks.get_dummies(kdf, dtype="float64")
        self.assert_eq(res, exp)

    def test_get_dummies_multiindex_columns(self):
        pdf = pd.DataFrame(
            {
                ("x", "a", "1"): [1, 2, 3, 4, 4, 3, 2, 1],
                ("x", "b", "2"): list("abcdabcd"),
                ("y", "c", "3"): list("abcdabcd"),
            }
        )
        kdf = ks.from_pandas(pdf)

        self.assert_eq(
            ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8).rename(columns=name_like_string)
        )
        self.assert_eq(
            ks.get_dummies(kdf, columns=[("y", "c", "3"), ("x", "a", "1")]),
            pd.get_dummies(pdf, columns=[("y", "c", "3"), ("x", "a", "1")], dtype=np.int8).rename(
                columns=name_like_string
            ),
        )
        self.assert_eq(
            ks.get_dummies(kdf, columns=["x"]),
            pd.get_dummies(pdf, columns=["x"], dtype=np.int8).rename(columns=name_like_string),
        )
        self.assert_eq(
            ks.get_dummies(kdf, columns=("x", "a")),
            pd.get_dummies(pdf, columns=("x", "a"), dtype=np.int8).rename(columns=name_like_string),
        )

        self.assertRaises(KeyError, lambda: ks.get_dummies(kdf, columns=["z"]))
        self.assertRaises(KeyError, lambda: ks.get_dummies(kdf, columns=("x", "c")))
        self.assertRaises(ValueError, lambda: ks.get_dummies(kdf, columns=[("x",), "c"]))
        self.assertRaises(TypeError, lambda: ks.get_dummies(kdf, columns="x"))

        # non-string names
        pdf = pd.DataFrame(
            {
                ("x", 1, "a"): [1, 2, 3, 4, 4, 3, 2, 1],
                ("x", 2, "b"): list("abcdabcd"),
                ("y", 3, "c"): list("abcdabcd"),
            }
        )
        kdf = ks.from_pandas(pdf)

        self.assert_eq(
            ks.get_dummies(kdf), pd.get_dummies(pdf, dtype=np.int8).rename(columns=name_like_string)
        )
        self.assert_eq(
            ks.get_dummies(kdf, columns=[("y", 3, "c"), ("x", 1, "a")]),
            pd.get_dummies(pdf, columns=[("y", 3, "c"), ("x", 1, "a")], dtype=np.int8).rename(
                columns=name_like_string
            ),
        )
        self.assert_eq(
            ks.get_dummies(kdf, columns=["x"]),
            pd.get_dummies(pdf, columns=["x"], dtype=np.int8).rename(columns=name_like_string),
        )
        self.assert_eq(
            ks.get_dummies(kdf, columns=("x", 1)),
            pd.get_dummies(pdf, columns=("x", 1), dtype=np.int8).rename(columns=name_like_string),
        )
