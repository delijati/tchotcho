import shutil
import tempfile
import pathlib
import unittest
import pytest
from unittest import mock

from tchotcho.__main__ import cli

HERE = pathlib.Path(__file__).absolute().parent
PRIVATE_KEY = HERE / "dummy"
DUMMY_REPO = HERE / "dummy_repo"


class TestShellKey(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def setUp(self):
        self.tmp_dir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_rsync(self):
        with pytest.raises(SystemExit) as ex:
            cli(["shell", "rsync", "--src", str(DUMMY_REPO), "--dst",
                 str(self.tmp_dir)])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue("total size is 4,780" in out)
        dst = self.tmp_dir / "dummy_repo"
        content = [p.name for p in dst.iterdir() if p.is_file()]
        self.assertEqual(content, ['README.md', '.gitignore', 'requirements.txt', 'main.py'])

    @mock.patch("subprocess.run")
    def test_ssh(self, patched_run):
        patched_run.return_value = mock.Mock(args=[], stderr=b"", returncode=0,
                                             stdout=b'/home/foo\nThu Jun  4 14:02:40 CEST 2020\n')
        with pytest.raises(SystemExit) as ex:
            cli(["shell", "ssh", "--privat-key", str(PRIVATE_KEY), "--host",
                 "localhost", "--cmd", "pwd ; date"])
        self.assertEqual(ex.value.code, 0)
        out, err = self.capsys.readouterr()
        self.assertTrue("/home/foo\nThu Jun  4 14:02:40 CEST 2020" in out)
