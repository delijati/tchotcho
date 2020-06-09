import unittest
import pathlib
from tchotcho.rsa import RSAFingerprintManager

PUB_KEY = pathlib.Path(__file__).absolute().parent / "dummy.pub.pem"
PRIV_KEY = pathlib.Path(__file__).absolute().parent / "dummy"


class TestRSAManager(unittest.TestCase):
    def test_extract(self):
        mgr = RSAFingerprintManager()
        pub = mgr.extract_private_to_public(PRIV_KEY)
        with open(PUB_KEY) as f:
            data = f.read()
        self.assertEqual(pub.split("\n")[1], data.split("\n")[1])
