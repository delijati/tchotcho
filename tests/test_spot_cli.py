import pathlib
import unittest
from unittest.mock import patch
import pytest

# from click.testing import CliRunner

from moto import mock_ec2
from tchotcho.__main__ import cli
from tchotcho.action.spot import SpotManager

IMPORT_KEY = pathlib.Path(__file__).absolute().parent / "dummy.pub"


@mock_ec2
class TestCliSpot(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    @patch.object(SpotManager, "_spot_history")
    def test_list(self, mocked_method):
        # XXX in moto describe_spot_price_history is not implemented and we
        # need the client to be initialized with the right version so we life
        # for now with that ugly patch
        mocked_method.return_value = [
            {
                "AvailabilityZone": "eu-central-1b",
                "InstanceType": "g3s.xlarge",
                "ProductDescription": "Linux/UNIX",
                "SpotPrice": "0.281400",
            },
            {
                "AvailabilityZone": "eu-central-1b",
                "InstanceType": "h3s.xlarge",
                "ProductDescription": "Linux/UNIX",
                "SpotPrice": "1.281400",
            },
            {
                "AvailabilityZone": "eu-central-1b",
                "InstanceType": "f3s.xlarge",
                "ProductDescription": "Linux/UNIX",
                "SpotPrice": "4.281400",
            },
        ]

        with pytest.raises(SystemExit) as ex:
            cli(
                [
                    "spot",
                    "list",
                    "--inst",
                    "g3s.xlarge",
                    "--region",
                    "eu-central-1",
                    "--csv",
                ]
            )
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue("0,g3s.xlarge,eu-central-1b,0.2814" in out)

        # color table
        with pytest.raises(SystemExit) as ex:
            cli(
                ["spot", "list", "--inst", "g3s.xlarge", "--region", "eu-central-1"]
            )
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue("\x1b[42m0.2814\x1b[49m" in out)
