import unittest
from core_engine import build_vlc_rc_command

class TestVlc(unittest.TestCase):
    def test_commands(self):
        self.assertEqual(build_vlc_rc_command("play"), "play\n")
        self.assertEqual(build_vlc_rc_command("volup", 2), "volup 2\n")

if __name__ == "__main__":
    unittest.main()
