import unittest

from parking.lot import ParkingLot
from parking.report import revenue_between


class ReportTest(unittest.TestCase):
    def test_revenue_between(self):
        history = [(10, "a", 30), (20, "b", 60), (30, "c", 90)]
        self.assertEqual(revenue_between(history, 15, 30), (150, 2))
        self.assertEqual(revenue_between(history, 0, 5), (0, 0))
        self.assertEqual(revenue_between([], 0, 100), (0, 0))

    def test_lot_revenue(self):
        lot = ParkingLot(1, 4)
        for i in range(4):
            lot.arrive("R%d" % i)
        lot.process_all(now=0)
        for i in range(4):
            lot.exit("R%d" % i, now=(i + 1) * 3600)
        self.assertEqual(lot.revenue_between(0, 2.5 * 3600), (90, 2))


if __name__ == "__main__":
    unittest.main()
