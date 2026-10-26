import unittest

from parking.graph import build_lot_graph, shortest_path, slot_distances


class GraphTest(unittest.TestCase):
    def test_shortest_path(self):
        g = build_lot_graph(2, 3)
        path, d = shortest_path(g, "入口", "F1-2")
        self.assertEqual(path, ["入口", "路口F0", "路口F1", "F1-2"])
        self.assertEqual(d, 21)

    def test_slot_distances_increase_with_index_and_floor(self):
        d = slot_distances(build_lot_graph(2, 3))
        self.assertEqual(d["F0-0"], 7)
        self.assertLess(d["F0-2"], d["F1-0"])
        self.assertEqual(len(d), 6)

    def test_unreachable_goal_raises(self):
        with self.assertRaises(ValueError):
            shortest_path({"A": [], "B": []}, "A", "B")


if __name__ == "__main__":
    unittest.main()
