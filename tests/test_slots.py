import unittest

from parking.slots import SlotManager


class SlotManagerTest(unittest.TestCase):
    def test_allocates_nearest_first(self):
        m = SlotManager(2, 3, {"F0-0": 7, "F0-1": 9, "F0-2": 11,
                               "F1-0": 17, "F1-1": 19, "F1-2": 21})
        names = [m.allocate().name for _ in range(6)]
        self.assertEqual(names, ["F0-0", "F0-1", "F0-2", "F1-0", "F1-1", "F1-2"])
        self.assertIsNone(m.allocate())

    def test_release_makes_slot_nearest_again(self):
        m = SlotManager(1, 3)
        a, b, _ = m.allocate(), m.allocate(), m.allocate()
        m.release(a)
        self.assertEqual(m.allocate().name, a.name)
        self.assertEqual(m.free_count(), 0)

    def test_get_slot_by_name(self):
        m = SlotManager(2, 3)
        self.assertEqual(m.get_slot("F1-2").name, "F1-2")


if __name__ == "__main__":
    unittest.main()
