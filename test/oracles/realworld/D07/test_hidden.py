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


class HiddenShutdownTests(unittest.TestCase):
    def test_shutdown_contract(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for this fixture")
        script = textwrap.dedent(r"""
            import assert from 'node:assert/strict';
            import {pathToFileURL} from 'node:url';
            const root = process.env.REALWORLD_ACTOR_ROOT;
            const {JobRunner} = await import(pathToFileURL(`${root}/worker/runner.js`));
        """) + FAKE_LIMIT + textwrap.dedent(r"""
            const runner = new JobRunner({concurrency: 2, createLimit});
            const started = [];
            const releases = [];
            const held = id => () => new Promise(resolve => {
              started.push(id);
              releases.push(() => resolve(id));
            });
            const first = runner.submit('first', held('first'));
            const second = runner.submit('second', held('second'));
            const third = runner.submit('third', async () => {
              started.push('third');
              return 'third';
            });
            await new Promise(resolve => setImmediate(resolve));
            assert.deepEqual(started, ['first', 'second'], 'requested concurrency was not preserved');
            const stopping = runner.shutdown();
            const late = runner.submit('late', async () => {
              started.push('late');
              return 'late';
            });
            releases.forEach(release => release());
            const timeout = new Promise(resolve => setTimeout(() => resolve('timeout'), 300));
            const outcomes = await Promise.race([stopping, timeout]);
            assert.notEqual(outcomes, 'timeout', 'shutdown did not finish');
            assert.deepEqual(outcomes.map(row => row.status), ['fulfilled', 'fulfilled', 'rejected']);
            assert.deepEqual(started, ['first', 'second'], 'queued work started after shutdown');
            assert.equal(await third.then(() => 'fulfilled', error => error.name), 'AbortError');
            assert.equal(await late.then(() => 'fulfilled', () => 'rejected'), 'rejected');

            const failing = new JobRunner({concurrency: 1, createLimit});
            let rejectBoom;
            const boom = failing.submit('boom', () => new Promise((resolve, reject) => {
              rejectBoom = () => reject(new Error('boom'));
            }));
            const cleared = failing.submit('cleared', async () => 'unexpected');
            const observedBoom = boom.then(() => '', error => error.message);
            const observedCleared = cleared.then(() => '', error => error.name);
            await new Promise(resolve => setImmediate(resolve));
            const failedStopping = failing.shutdown();
            rejectBoom();
            const failedOutcomes = await failedStopping;
            assert.deepEqual(failedOutcomes.map(row => row.status), ['rejected', 'rejected']);
            assert.equal(await observedBoom, 'boom');
            assert.equal(await observedCleared, 'AbortError');
            console.log(JSON.stringify({ok: true}));
        """)
        completed = subprocess.run(
            [node, "--input-type=module", "--eval", script],
            env=os.environ.copy(), capture_output=True, text=True, timeout=6,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout.strip()), {"ok": True})


if __name__ == "__main__":
    unittest.main()
