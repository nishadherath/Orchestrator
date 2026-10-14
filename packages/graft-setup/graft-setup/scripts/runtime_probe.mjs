// Local build features, queried from the selected Graft rather than its label.
// No provider call, update check, source read or host registration.
import {pathToFileURL} from 'node:url';
import {resolve, dirname, join} from 'node:path';
const entry = resolve(process.argv[2]);
const dist = dirname(entry);
try {
  const memo = await import(pathToFileURL(join(dist, 'graph/extract-cache.js')).href);
  const fingerprint = await import(pathToFileURL(join(dist, 'graph/fingerprint.js')).href);
  const walk = await import(pathToFileURL(join(dist, 'ingest/fs.js')).href);
  const check = await import(pathToFileURL(join(dist, 'graph/check.js')).href);
  console.log(JSON.stringify({available:true, extractor_stamp:memo.extractorStamp(),
    preserves_foreign_scope:typeof fingerprint.readFingerprintScope === 'function',
    prunes_scoped_walk:walk.SCOPED_WALK_VERSION === 1,
    hash_checked_memo:check.HASH_CHECKED_MEMO_VERSION === 1}));
} catch {
  console.log(JSON.stringify({available:false, reason:'This build does not expose the inspected local modules.'}));
}
