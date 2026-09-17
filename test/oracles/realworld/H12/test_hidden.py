import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from adapter.codec import decode, encode


class HiddenCodecTests(unittest.TestCase):
    def test_legacy_contract_survives(self):
        self.assertEqual(encode("world",legacy=True),b"v1:world")
        self.assertEqual(decode(b"v1:world"),"world")

    def test_new_frame_uses_length_and_validates_it(self):
        self.assertEqual(encode("world"),b"v2:5|world")
        self.assertEqual(decode(b"v2:5|world"),"world")
        with self.assertRaises(ValueError): decode(b"v2:4|world")


if __name__ == "__main__": unittest.main()
