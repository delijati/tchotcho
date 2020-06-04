import pathlib
import json
import tempfile
import unittest
import unittest.mock

import pytest

# from click.testing import CliRunner
from moto import mock_ec2
from tchotcho.config import set_settings, Settings
from tchotcho.__main__ import cli

HERE = pathlib.Path(__file__).absolute().parent

GPU_INFO_FILE = HERE / "gpu_info.json"
INSTANCES = HERE / "instances-slim.json"


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    with open(INSTANCES, "r") as f:
        data = json.load(f)
    return MockResponse(data, 200)


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

    @unittest.mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_create(self, mock_get):
        with tempfile.NamedTemporaryFile() as tmp_gpu_info:
            settings = Settings()
            settings.GPU_INFO_FILE = tmp_gpu_info.name
            set_settings(settings)

            with pytest.raises(SystemExit) as ex:
                cli(
                    [
                        "info",
                        "update",
                        "--csv",
                        "--region",
                        "us-east-2",
                        "--namefilter",
                        "ubuntu*",
                        "--ownerid",
                        "099720109477",
                    ]
                )
            self.assertTrue(mock_get.called)
            self.assertEqual(ex.value.code, 0)
            out, err = self.capsys.readouterr()
            self.assertTrue("g2.8xlarge,4,32,NVIDIA GRID K520" in out)

    def test_list(self):
        with pytest.raises(SystemExit) as ex:
            cli(["info", "list", "--region", "eu-central-1", "--csv"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue("g2.8xlarge,4,32,NVIDIA GRID K520" in out)

        # color table
        with pytest.raises(SystemExit) as ex:
            cli(["info", "list", "--region", "eu-central-1"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue("\x1b[43m2.85\x1b[49m" in out)
