import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

ACTOR = Path(os.environ["REALWORLD_ACTOR_ROOT"])


class HiddenPackageTests(unittest.TestCase):
    def test_declared_files_load_in_clean_consumer(self):
        package = json.loads((ACTOR / "package.json").read_text())
        self.assertEqual(package.get("supportedFormats"), ["commonjs"])
        with tempfile.TemporaryDirectory() as folder:
            consumer = Path(folder) / "node_modules" / package["name"]
            consumer.mkdir(parents=True)
            shutil.copy2(ACTOR / "package.json", consumer / "package.json")
            for name in package["files"]:
                source = ACTOR / name
                if source.is_dir(): shutil.copytree(source, consumer / name)
            script = "const p=require(process.argv[1]); console.log(p.sum(7,8))"
            result = subprocess.run(["node", "-e", script, str(consumer)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "15")


if __name__ == "__main__": unittest.main()
