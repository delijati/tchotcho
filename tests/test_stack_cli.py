import unittest
import pytest

# from click.testing import CliRunner

from moto import mock_cloudformation, mock_ec2
from tchotcho.__main__ import cli

# from tchotcho.action.stack import StackManager


@mock_cloudformation
@mock_ec2
class TestCliStack(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def setUp(self):
        import requests

        # reset moto or we have to many clouds
        requests.post("http://motoapi.amazonaws.com/moto-api/reset")

    def test_create_dry(self):
        with pytest.raises(SystemExit) as ex:
            cli(
                [
                    "stack",
                    "create",
                    "--name",
                    "test-key",
                    "--inst",
                    "t2.medium",
                    "--price",
                    "0.02",
                    "--ami",
                    # XXX an image listed in moto
                    "ami-1e749f67",
                    "--dry",
                ]
            )
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue("Availability Zone of the EC2 instance" in out)

    def test_list(self):
        with pytest.raises(SystemExit) as ex:
            cli(["stack", "list", "--csv"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertEqual("No stacks found!\n", out)
