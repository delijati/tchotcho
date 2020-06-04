import shutil
import tempfile
import pathlib
import unittest
import pytest

# from click.testing import CliRunner

from moto import mock_ec2
from tchotcho.config import set_settings, Settings
from tchotcho.__main__ import cli

IMPORT_KEY = pathlib.Path(__file__).absolute().parent / "dummy.pub"


@mock_ec2
class TestCliKey(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def setUp(self):
        import requests

        # reset moto or we have to many keys
        requests.post("http://motoapi.amazonaws.com/moto-api/reset")
        settings = Settings()
        self.tmp_dir = pathlib.Path(tempfile.mkdtemp())
        settings.PROG_HOME = self.tmp_dir
        set_settings(settings)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def _create(self, name):
        with pytest.raises(SystemExit):
            cli(["key", "create", "--name", name])
        out, err = self.capsys.readouterr()

    def test_create(self):
        with pytest.raises(SystemExit) as ex:
            cli(["key", "create", "--name", "test-key"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertEqual(out, "Succesfully created key test-key\n")

    def test_list(self):
        self._create("test-key")

        with pytest.raises(SystemExit) as ex:
            cli(["key", "list", "--name", "test-key", "--csv"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue('{"KeyName":{"0":"test-key"},"KeyFi' in out)

        # color table
        with pytest.raises(SystemExit) as ex:
            cli(["key", "list", "--name", "test-key"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue("\x1b[42mtest-key\x1b[49m" in out)

    def test_import(self):
        with pytest.raises(SystemExit) as ex:
            cli(["key", "import", "--name", "test-key", "--path", IMPORT_KEY])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertEqual(out, "Succesfully imported key test-key\n")

    def test_delete(self):
        self._create("test-key")

        with pytest.raises(SystemExit) as ex:
            cli(["key", "delete", "--name", "test-key", "--no-ask"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertEqual(out, "Succesfully deleted key test-key\n")

    def test_fingerprint(self):
        with pytest.raises(SystemExit) as ex:
            cli(
                [
                    "key",
                    "fingerprint",
                    "--path",
                    IMPORT_KEY,
                    "--passphrase",
                    "",
                    "--csv",
                ]
            )
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue('{"public":{"0":"1a:5a:45:33:a1:f8:28:a7:f' in out)
