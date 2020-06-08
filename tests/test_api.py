import unittest

from moto import mock_ec2
from tchotcho import (InfoManager, KeyManager, ShellManager, SpotManager,
                      StackManager)


@mock_ec2
class TestApi(unittest.TestCase):

    def test_import(self):
        self.assertIsInstance(KeyManager(), KeyManager)
        self.assertIsInstance(StackManager(), StackManager)
        self.assertIsInstance(SpotManager(), SpotManager)
        self.assertIsInstance(InfoManager(), InfoManager)
        self.assertIsInstance(ShellManager(), ShellManager)
