import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from photosort import core  # noqa: E402


def touch(p: Path, data: bytes = b"x", mtime: float | None = None) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    if mtime:
        os.utime(p, (mtime, mtime))


class CoreTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.d = Path(self._t.name)

    def tearDown(self):
        self._t.cleanup()

    def sample(self):
        for n in ("DSC0001.JPG", "DSC0001.ARW", "DSC0002.jpg", "DSC0003.ARW", "notes.txt", "._DSC0001.ARW"):
            touch(self.d / n)

    def test_copy_split(self):
        self.sample()
        o = core.Options()
        plan = core.build_plan(self.d, o)
        self.assertEqual((plan.jpg_count, plan.raw_count, plan.pairs), (2, 2, 1))
        self.assertEqual([p.name for p in plan.jpg_only], ["DSC0002.jpg"])
        self.assertEqual([p.name for p in plan.raw_only], ["DSC0003.ARW"])
        res = core.execute(plan, o)
        self.assertEqual(res.done, 4)
        self.assertTrue((self.d / "JPG" / "DSC0001.JPG").exists())
        self.assertTrue((self.d / "RAW" / "DSC0001.ARW").exists())
        self.assertTrue((self.d / "DSC0001.JPG").exists())  # 복사: 원본 유지
        self.assertFalse((self.d / "RAW" / "._DSC0001.ARW").exists())

    def test_move(self):
        self.sample()
        o = core.Options(move=True)
        core.execute(core.build_plan(self.d, o), o)
        self.assertFalse((self.d / "DSC0001.JPG").exists())
        self.assertTrue((self.d / "RAW" / "DSC0003.ARW").exists())

    def test_rerun_is_noop(self):
        self.sample()
        o = core.Options()
        core.execute(core.build_plan(self.d, o), o)
        self.assertEqual(core.build_plan(self.d, o).items, [])

    def test_name_conflict_not_overwritten(self):
        touch(self.d / "JPG" / "A.JPG", b"old")
        touch(self.d / "A.JPG", b"new-different")
        o = core.Options()
        core.execute(core.build_plan(self.d, o), o)
        self.assertEqual((self.d / "JPG" / "A.JPG").read_bytes(), b"old")
        self.assertEqual((self.d / "JPG" / "A_1.JPG").read_bytes(), b"new-different")

    def test_by_date_and_recursive(self):
        touch(self.d / "DCIM" / "100MSDCF" / "B.ARW", mtime=1760400000)  # 2025-10-14 UTC
        o = core.Options(by_date=True, recursive=True)
        plan = core.build_plan(self.d, o)
        self.assertEqual(plan.raw_count, 1)
        self.assertRegex(str(plan.items[0].dst), r"\d{4}-\d{2}-\d{2}/RAW/B\.ARW$")
        self.assertEqual(core.build_plan(self.d, core.Options()).items, [])  # 비재귀면 안 봄


if __name__ == "__main__":
    unittest.main()
