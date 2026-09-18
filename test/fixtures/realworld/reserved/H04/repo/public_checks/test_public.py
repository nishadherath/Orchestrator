import os, subprocess, unittest


class PackageTests(unittest.TestCase):
    def test_source_checkout_loads(self):
        root = os.environ["REALWORLD_ACTOR_ROOT"]
        result = subprocess.run(["node", "-e", "console.log(require(process.argv[1]).sum(2,3))", root], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "5"))


if __name__ == "__main__": unittest.main()
