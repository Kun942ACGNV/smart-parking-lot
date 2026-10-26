import unittest

from parking.lot import ParkingLot

H = 3600


class ParkingLotTest(unittest.TestCase):
    def make_full_lot(self):
        lot = ParkingLot(2, 2)
        for p in ["A1", "A2", "A3", "A4", "A5"]:
            lot.arrive(p)
        lot.process_all(now=0)
        return lot

    def test_full_lot_queues_extra_car(self):
        lot = self.make_full_lot()
        self.assertEqual(lot.status(),
                         {"total": 4, "occupied": 4, "free": 0, "waiting": 1})

    def test_duplicate_plate_rejected(self):
        lot = self.make_full_lot()
        with self.assertRaises(ValueError):
            lot.arrive("A1")          # 已在場內
        with self.assertRaises(ValueError):
            lot.arrive("A5")          # 正在排隊
        with self.assertRaises(ValueError):
            lot.arrive("")

    def test_exit_lets_waiting_car_take_freed_slot(self):
        lot = self.make_full_lot()
        freed = lot.find("A1")
        lot.exit("A1", now=1800)
        ticket = lot.process_entry(now=1800)
        self.assertEqual(ticket.plate, "A5")
        self.assertEqual(ticket.slot.name, freed)

    def test_fee_rounding(self):
        cases = [(0, 30), (1, 30), (30 * 60, 30), (H, 30),
                 (H + 1, 60), (int(2.5 * H), 90), (3 * H, 90)]
        for seconds, fee in cases:
            lot = ParkingLot(1, 2)
            lot.arrive("X")
            lot.process_entry(now=0)
            self.assertEqual(lot.exit("X", now=seconds).fee, fee, seconds)

    def test_exit_unknown_plate_raises(self):
        with self.assertRaises(KeyError):
            ParkingLot(1, 1).exit("NOPE")

    def test_trie_follows_entry_and_exit(self):
        lot = ParkingLot(1, 3)
        for p in ["ABC-1", "ABC-2"]:
            lot.arrive(p)
        lot.process_all(now=0)
        self.assertEqual([p for p, _ in lot.search("ABC")], ["ABC-1", "ABC-2"])
        lot.exit("ABC-1", now=10)
        self.assertEqual([p for p, _ in lot.search("ABC")], ["ABC-2"])

    def test_route_to(self):
        lot = ParkingLot(2, 3)
        for i in range(4):
            lot.arrive("C%d" % i)
        lot.process_all(now=0)
        path, d = lot.route_to("C3")        # 第 4 輛 → F1-0
        self.assertEqual(path[-1], "F1-0")
        self.assertEqual(d, 17)


if __name__ == "__main__":
    unittest.main()
