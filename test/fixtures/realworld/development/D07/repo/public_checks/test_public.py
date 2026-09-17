import json
import os
import shutil
import subprocess
import textwrap
import unittest


FAKE_LIMIT = r"""
function createLimit(setting) {
  const options = typeof setting === 'number'
    ? {concurrency: setting, rejectOnClear: false}
    : {rejectOnClear: false, ...setting};
  let active = 0;
  const queue = [];
  const pump = () => {
    while (active < options.concurrency && queue.length > 0) {
      const entry = queue.shift();
      active += 1;
      Promise.resolve().then(entry.work).then(entry.resolve, entry.reject).finally(() => {
        active -= 1;
        pump();
      });
    }
  };
  const limit = work => new Promise((resolve, reject) => {
    queue.push({work, resolve, reject});
    queueMicrotask(pump);
  });
  limit.clearQueue = () => {
    const pending = queue.splice(0);
    if (options.rejectOnClear) {
      for (const entry of pending) {
        const error = new Error('Job was cleared');
        error.name = 'AbortError';
        entry.reject(error);
      }
    }
  };
  Object.defineProperties(limit, {
    activeCount: {get: () => active},
    pendingCount: {get: () => queue.length},
  });
  return limit;
}
"""


class PublicShutdownTests(unittest.TestCase):
    def test_shutdown_drains_running_and_rejects_queued(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for this fixture")
        script = textwrap.dedent(r"""
            import {pathToFileURL} from 'node:url';
            const root = process.env.REALWORLD_ACTOR_ROOT;
            const {JobRunner} = await import(pathToFileURL(`${root}/worker/runner.js`));
        """) + FAKE_LIMIT + textwrap.dedent(r"""
            const runner = new JobRunner({concurrency: 1, createLimit});
            let release;
            const started = [];
            const first = runner.submit('running', () => new Promise(resolve => {
              started.push('running');
              release = () => resolve('done');
            }));
            const second = runner.submit('queued', async () => {
              started.push('queued');
              return 'unexpected';
            });
            await new Promise(resolve => setImmediate(resolve));
            const stopping = runner.shutdown();
            release();
            const timeout = new Promise(resolve => setTimeout(() => resolve('timeout'), 250));
            const outcomes = await Promise.race([stopping, timeout]);
            const secondOutcome = await Promise.race([
              second.then(() => 'fulfilled', error => error.name),
              new Promise(resolve => setTimeout(() => resolve('pending'), 50)),
            ]);
            await first;
            console.log(JSON.stringify({outcomes, secondOutcome, started}));
        """)
        completed = subprocess.run(
            [node, "--input-type=module", "--eval", script],
            env=os.environ.copy(), capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout.strip())
        self.assertNotEqual(result["outcomes"], "timeout")
        self.assertEqual([row["status"] for row in result["outcomes"]],
                         ["fulfilled", "rejected"])
        self.assertEqual(result["secondOutcome"], "AbortError")
        self.assertEqual(result["started"], ["running"])


if __name__ == "__main__":
    unittest.main()
