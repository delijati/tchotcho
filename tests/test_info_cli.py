import pathlib
import unittest
import pytest

# from click.testing import CliRunner

from moto import mock_ec2
from tchotcho.config import set_settings, Settings
from tchotcho.__main__ import cli

GPU_INFO_FILE = pathlib.Path(__file__).absolute().parent / "gpu_info.json"


@mock_ec2
class TestInfoKey(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def setUp(self):
        import requests
        # reset moto or we have to many keys
        requests.post("http://motoapi.amazonaws.com/moto-api/reset")
        settings = Settings()
        settings.GPU_INFO_FILE = GPU_INFO_FILE
        set_settings(settings)

    def test_list(self):
        with pytest.raises(SystemExit) as ex:
            cli(["info", "list", "--region", "eu-central-1", "--csv"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue('g2.8xlarge,4,32,NVIDIA GRID K520' in out)
