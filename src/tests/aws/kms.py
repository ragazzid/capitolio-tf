import unittest
import aws.kms as kms
import base64


class TestKms(unittest.TestCase):
    def test_Base64_d(self):
        d = b"randonStringBlabla"
        t = base64.b64encode(d)
        t = kms.base64_d(t)
        self.assertEqual(d, t)


if __name__ == "__main__":
    unittest.main()