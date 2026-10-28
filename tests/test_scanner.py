import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from wincachesweep.scanner import DiskScanner, FileItem, ScanTarget, purge_items


class TestDiskScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Create dummy files
        self.old_file = self.dir_path / "old_temp.tmp"
        self.old_file.write_bytes(b"A" * 1024)
        old_time = (datetime.now() - timedelta(days=30)).timestamp()
        os.utime(self.old_file, (old_time, old_time))

        self.new_file = self.dir_path / "new_temp.tmp"
        self.new_file.write_bytes(b"B" * 2048)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_known_targets_returns_list(self):
        targets = DiskScanner.get_known_targets()
        self.assertIsInstance(targets, list)
        self.assertTrue(len(targets) > 0)

    def test_scan_location(self):
        scanner = DiskScanner(stale_days=14)
        target = ScanTarget(
            name="Test Target",
            path=self.dir_path,
            category="User Temp",
            safety_level="SAFE",
            description="Test temporary folder",
        )

        items = scanner.scan_location(target)
        self.assertEqual(len(items), 2)

        # Ensure staleness rating check works
        old_items = [i for i in items if i.path.name == "old_temp.tmp"]
        new_items = [i for i in items if i.path.name == "new_temp.tmp"]

        self.assertEqual(len(old_items), 1)
        self.assertEqual(old_items[0].safety_level, "SAFE")

        self.assertEqual(len(new_items), 1)
        self.assertEqual(new_items[0].safety_level, "CAUTION")

    def test_purge_dry_run(self):
        item = FileItem(
            path=self.old_file,
            size_bytes=1024,
            modified_time=datetime.now(),
            category="User Temp",
            safety_level="SAFE",
            reason="Test",
        )
        reclaimed, count = purge_items([item], dry_run=True)
        self.assertEqual(reclaimed, 1024)
        self.assertEqual(count, 1)
        self.assertTrue(self.old_file.exists())

    def test_purge_execution(self):
        item = FileItem(
            path=self.old_file,
            size_bytes=1024,
            modified_time=datetime.now(),
            category="User Temp",
            safety_level="SAFE",
            reason="Test",
        )
        reclaimed, count = purge_items([item], dry_run=False)
        self.assertEqual(reclaimed, 1024)
        self.assertEqual(count, 1)
        self.assertFalse(self.old_file.exists())


if __name__ == "__main__":
    unittest.main()
