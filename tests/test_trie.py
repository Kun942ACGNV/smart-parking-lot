import unittest

from parking.trie import PlateTrie


class PlateTrieTest(unittest.TestCase):
    def setUp(self):
        self.t = PlateTrie()
        for p in ["ABC-123", "ABC-456", "ABD-555", "XYZ-789"]:
            self.t.insert(p)

    def test_prefix_search_sorted(self):
        self.assertEqual(self.t.search_prefix("ABC"), ["ABC-123", "ABC-456"])
        self.assertEqual(self.t.search_prefix("A"),
                         ["ABC-123", "ABC-456", "ABD-555"])
        self.assertEqual(self.t.search_prefix("ZZ"), [])

    def test_delete(self):
        self.t.delete("ABC-123")
        self.assertEqual(self.t.search_prefix("ABC"), ["ABC-456"])

    def test_delete_keeps_longer_word_sharing_prefix(self):
        t = PlateTrie()
        t.insert("AB")
        t.insert("ABC")
        t.delete("AB")
        self.assertEqual(t.search_prefix("AB"), ["ABC"])

    def test_delete_missing_is_safe(self):
        self.t.delete("NOPE")
        self.assertEqual(len(self.t.search_prefix("")), 4)


if __name__ == "__main__":
    unittest.main()
