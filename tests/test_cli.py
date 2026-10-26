import contextlib
import io
import unittest
from unittest import mock

from parking.cli import main


def run_cli(inputs):
    out = io.StringIO()
    with mock.patch("builtins.input", side_effect=inputs):
        with contextlib.redirect_stdout(out):
            code = main([])
    return code, out.getvalue()


class CliSmokeTest(unittest.TestCase):
    def test_demo_then_status(self):
        code, text = run_cli(["9", "6", "0"])
        self.assertEqual(code, 0)
        self.assertIn("ABC-123 入場 → 車位 F0-0", text)
        self.assertIn("使用中 5", text)

    def test_fast_forward_and_fee(self):
        code, text = run_cli(["9", "8", "2.5", "3", "ABC-123", "0"])
        self.assertIn("計費 3 小時｜應收 90 元", text)

    def test_queue_and_auto_fill(self):
        inputs = ["9"]
        for p in ["F1", "F2", "F3"]:
            inputs += ["1", p]
        inputs += ["2", "1", "WAIT-1", "2", "3", "ABC-456", "0"]
        _, text = run_cli(inputs)
        self.assertIn("仍有 1 輛在排隊", text)
        self.assertIn("排隊車輛 WAIT-1 自動進入釋出的車位 F0-1", text)

    def test_invalid_choice_and_eof(self):
        code, text = run_cli(["x", EOFError()])   # 之後 EOF → 視為離開
        self.assertIn("無效的選項", text)


if __name__ == "__main__":
    unittest.main()
