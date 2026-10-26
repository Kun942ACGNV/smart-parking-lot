import os
import tempfile
import unittest

from parking.lot import ParkingLot
from parking.storage import load_state, save_state


class StorageTest(unittest.TestCase):
    def test_roundtrip(self):
        lot = ParkingLot(2, 2)
        for p in ["S1", "S2", "S3", "S4", "S5"]:
            lot.arrive(p)
        lot.process_all(now=100)
        lot.exit("S2", now=4000)
        lot.arrive("S6")
        lot.process_all(now=4000)

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "state.json")
            save_state(lot, path)
            restored = load_state(path)

        self.assertEqual(restored.status(), lot.status())
        self.assertEqual(sorted(restored.active), sorted(lot.active))
        self.assertEqual(list(restored.entry_queue), list(lot.entry_queue))
        self.assertEqual(restored.history, lot.history)
        # 還原後堆積與 Trie 仍可正常運作
        restored.exit("S1", now=9000)
        self.assertEqual(restored.mgr.free_count(), 1)
        self.assertNotIn("S1", [p for p, _ in restored.search("S")])


if __name__ == "__main__":
    unittest.main()
