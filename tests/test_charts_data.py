import unittest

import numpy as np

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.presentation.charts import (
    _consolidated_3d_data,
    _daily_3d_data,
    _interpolate_3d_surface,
    _interpolate_rates,
    _nearest_rate,
    _nearest_ticks,
)


def _records(*pairs):
    return [
        RateRecord(day252=d, day360=d, rate=str(r).replace(".", ","))
        for d, r in pairs
    ]


class NearestTicksTest(unittest.TestCase):
    def test_returns_nearest_within_tolerance(self):
        self.assertEqual(_nearest_ticks([1, 22, 45, 66], range(1, 67, 22), 12), [1, 22, 45])

    def test_excludes_duplicates(self):
        result = _nearest_ticks([10, 11, 30, 31], range(10, 32, 20), 2)
        self.assertEqual(result, [10, 30])

    def test_boundary_tolerance_inclusive(self):
        self.assertEqual(_nearest_ticks([10], range(12), 2), [10])
        self.assertEqual(_nearest_ticks([10], range(12), 1), [10])

    def test_out_of_tolerance_skipped(self):
        self.assertEqual(_nearest_ticks([100], range(1, 10), 1), [])

    def test_exclude_set_skipped(self):
        result = _nearest_ticks([1, 22, 45], range(0, 46, 21), 3, {22})
        self.assertEqual(result, [1, 45])


class InterpolateRatesTest(unittest.TestCase):
    def test_interpolates_linear(self):
        records = _records((0, 14.0), (10, 16.0))
        result = _interpolate_rates(records, np.array([0.0, 5.0, 10.0]))
        np.testing.assert_allclose(result, [14.0, 15.0, 16.0])

    def test_left_right_nan(self):
        records = _records((5, 15.0), (10, 17.0))
        result = _interpolate_rates(records, np.array([0.0, 5.0, 10.0, 15.0]))
        self.assertTrue(np.isnan(result[0]))
        self.assertTrue(np.isnan(result[3]))

    def test_comma_decimal(self):
        records = [RateRecord(day252=0, day360=0, rate="14,5")]
        result = _interpolate_rates(records, np.array([0.0]))
        np.testing.assert_allclose(result, [14.5])


class NearestRateTest(unittest.TestCase):
    def test_within_tolerance(self):
        rates = {10: 14.5, 22: 15.0, 33: 16.0}
        self.assertEqual(_nearest_rate(rates, 23, 2), 15.0)

    def test_boundary_tolerance_inclusive(self):
        rates = {10: 14.5}
        self.assertEqual(_nearest_rate(rates, 12, 2), 14.5)
        self.assertIsNone(_nearest_rate(rates, 13, 2))

    def test_out_of_tolerance_none(self):
        rates = {10: 14.5}
        self.assertIsNone(_nearest_rate(rates, 50, 2))


class Consolidated3dDataTest(unittest.TestCase):
    def test_years_filtered_to_0_20(self):
        date_rates = {
            "2026-01-01": _records((1, 14.0), (30, 15.0), (365, 16.0)),
            "2026-01-02": _records((1, 14.5), (30, 15.5), (365, 16.5)),
        }
        per_date, X, Z = _consolidated_3d_data(date_rates, sorted(date_rates))
        self.assertEqual(len(per_date), 2)
        self.assertEqual(X.shape[0], 2)
        self.assertEqual(Z.shape[0], 2)
        self.assertEqual(X.shape[1], Z.shape[1])
        self.assertTrue(np.all(X == X.astype(int)))
        self.assertFalse(np.isnan(Z).all())

    def test_year_zero_included(self):
        date_rates = {
            "2026-01-01": _records((1, 14.0), (365, 15.0)),
            "2026-01-02": _records((1, 14.5), (365, 15.5)),
        }
        per_date, X, Z = _consolidated_3d_data(date_rates, sorted(date_rates))
        self.assertIn(0, X[0])

    def test_year_21_excluded(self):
        date_rates = {
            "2026-01-01": _records((1, 14.0), (366 * 21, 15.0)),
            "2026-01-02": _records((1, 14.5), (366 * 21, 15.5)),
        }
        per_date, X, Z = _consolidated_3d_data(date_rates, sorted(date_rates))
        self.assertNotIn(21, X[0])

    def test_year_20_included(self):
        date_rates = {
            "2026-01-01": _records((1, 14.0), (366 * 20, 15.0)),
            "2026-01-02": _records((1, 14.5), (366 * 20, 15.5)),
        }
        per_date, X, Z = _consolidated_3d_data(date_rates, sorted(date_rates))
        self.assertIn(20, X[0])

    def test_missing_year_is_nan(self):
        date_rates = {
            "2026-01-01": _records((1, 14.0), (365, 15.0)),
            "2026-01-02": _records((1, 14.5), (365, 15.5), (730, 16.5)),
        }
        per_date, X, Z = _consolidated_3d_data(date_rates, sorted(date_rates))
        year2_idx = list(X[0]).index(2)
        self.assertTrue(np.isnan(Z[0, year2_idx]))


class Daily3dDataTest(unittest.TestCase):
    def test_basic_structure(self):
        date_rates = {
            "2026-01-01": _records((1, 14.0), (365, 15.0)),
            "2026-01-02": _records((1, 14.5), (365, 15.5)),
        }
        per_date, X, Z = _daily_3d_data(date_rates, sorted(date_rates))
        self.assertEqual(len(per_date), 2)
        self.assertEqual(Z.shape[0], 2)
        self.assertEqual(Z.shape[1], 200)

    def test_day_756_included(self):
        date_rates = {
            "2026-01-01": _records((1, 14.0), (756, 15.0)),
            "2026-01-02": _records((1, 14.5), (756, 15.5)),
        }
        per_date, X, Z = _daily_3d_data(date_rates, sorted(date_rates))
        days = per_date[0][0]
        self.assertIn(756, days)

    def test_day_757_excluded(self):
        date_rates = {
            "2026-01-01": _records((1, 14.0), (757, 15.0)),
            "2026-01-02": _records((1, 14.5), (757, 15.5)),
        }
        per_date, X, Z = _daily_3d_data(date_rates, sorted(date_rates))
        days = per_date[0][0]
        self.assertNotIn(757, days)

    def test_empty_all_days_raises_or_empty_grid(self):
        date_rates = {
            "2026-01-01": _records(),
            "2026-01-02": _records(),
        }
        try:
            per_date, X, Z = _daily_3d_data(date_rates, sorted(date_rates))
            self.assertEqual(X.shape, (2, 200))
        except ValueError:
            pass
    def test_interp_values(self):
        date_rates = {
            "2026-01-01": _records((0, 14.0), (100, 16.0)),
            "2026-01-02": _records((0, 14.5), (100, 16.5)),
        }
        per_date, X, Z = _daily_3d_data(date_rates, sorted(date_rates))
        self.assertFalse(np.isnan(Z[0]).any())
        self.assertAlmostEqual(Z[0][0], 14.0, places=1)
        self.assertAlmostEqual(Z[0][-1], 16.0, places=1)

    def test_grid_starts_at_zero(self):
        date_rates = {
            "2026-01-01": _records((10, 14.0), (100, 16.0)),
            "2026-01-02": _records((10, 14.5), (100, 16.5)),
        }
        per_date, X, Z = _daily_3d_data(date_rates, sorted(date_rates))
        self.assertEqual(X[0][0], 0.0)

    def test_out_of_range_returns_nan(self):
        date_rates = {
            "2026-01-01": _records((10, 14.0), (100, 16.0)),
            "2026-01-02": _records((10, 14.5), (100, 16.5)),
        }
        per_date, X, Z = _daily_3d_data(date_rates, sorted(date_rates))
        self.assertTrue(np.isnan(Z[0][0]))
        self.assertAlmostEqual(Z[0][-1], 16.0, places=1)


class Interpolate3dSurfaceTest(unittest.TestCase):
    def _sample(self):
        X = np.array([[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]])
        Z = np.array([[10.0, 20.0], [12.0, 22.0], [14.0, 24.0]])
        return X, Z, [0, 1, 2]

    def test_shapes(self):
        X_f, Y_f, Z_f = _interpolate_3d_surface(*self._sample())
        self.assertEqual(Y_f.shape, (60, 2))
        self.assertEqual(X_f.shape, Y_f.shape)
        self.assertEqual(Z_f.shape, Y_f.shape)

    def test_two_good_points_interpolates(self):
        X_f, Y_f, Z_f = _interpolate_3d_surface(*self._sample())
        # first column: 10,12,14 across z -> at z=1.0 should be ~12
        value = np.interp(1.0, Y_f[:, 0], Z_f[:, 0])
        self.assertAlmostEqual(value, 12.0, places=6)

    def test_single_good_point_constant(self):
        X = np.array([[0.0, 1.0], [0.0, 1.0]])
        Z = np.array([[10.0, np.nan], [np.nan, np.nan]])
        X_f, Y_f, Z_f = _interpolate_3d_surface(X, Z, [0, 1])
        self.assertAlmostEqual(Z_f[0, 0], 10.0, places=6)
        self.assertTrue(np.isnan(Z_f[0, 1]))

    def test_no_good_points_nan(self):
        X = np.array([[0.0, 1.0], [0.0, 1.0]])
        Z = np.array([[np.nan, np.nan], [np.nan, np.nan]])
        X_f, Y_f, Z_f = _interpolate_3d_surface(X, Z, [0, 1])
        self.assertTrue(np.isnan(Z_f[:, 0]).all())
        self.assertTrue(np.isnan(X_f[:, 1]).all())

    def test_exactly_two_good_points(self):
        X = np.array([[0.0, 1.0], [5.0, 6.0], [np.nan, 7.0]])
        Z = np.array([[10.0, np.nan], [12.0, np.nan], [np.nan, np.nan]])
        X_f, Y_f, Z_f = _interpolate_3d_surface(X, Z, [0, 1, 2])
        self.assertFalse(np.isnan(Z_f[:, 0]).any())
        self.assertTrue(np.isnan(Z_f[:, 1]).all())
        # middle value interpolated (not constant): ~12 at z=1
        value = np.interp(1.0, Y_f[:, 0], Z_f[:, 0])
        self.assertAlmostEqual(value, 12.0, places=1)
        self.assertGreater(value, 10.0)
        self.assertLess(value, 14.0)
        # X interpolated across good points
        xvalue = np.interp(1.0, Y_f[:, 0], X_f[:, 0])
        self.assertAlmostEqual(xvalue, 5.0, places=1)

    def test_single_good_point_constant_x(self):
        X = np.array([[3.0, 1.0], [np.nan, 2.0]])
        Z = np.array([[10.0, np.nan], [np.nan, np.nan]])
        X_f, Y_f, Z_f = _interpolate_3d_surface(X, Z, [0, 1])
        self.assertTrue(np.isnan(Z_f[:, 1]).all())
        self.assertAlmostEqual(Z_f[0, 0], 10.0, places=6)
        self.assertAlmostEqual(X_f[0, 0], 3.0, places=6)


if __name__ == "__main__":
    unittest.main()
