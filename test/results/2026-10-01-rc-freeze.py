"""Freeze and verify the unpublished RC without changing Git history or spending."""
from __future__ import annotations
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'test/results/2026-10-01-rc'
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'test/harness'))
import build_dist
import release_check
from worker_executor_consumer_tests import SCRIPT
from worker_n8_consumer_tests import CLI_SCRIPT

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()

def files_at(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise RuntimeError(f'redirected snapshot path: {p}')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
            result[p.relative_to(root).as_posix()] = p.read_bytes()
    return result

def archive(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw)
    return buf.getvalue()

def save_once(path, raw):
    if path.exists() and path.read_bytes() != raw:
        raise RuntimeError(f'frozen artifact differs: {path}; use a new candidate')
    path.write_bytes(raw)

def invoke(bundle, action, target, *args, expected=0):
    proc = subprocess.run([sys.executable, str(bundle / 'install.py'), action,
        '--target', str(target), '--bundle', str(bundle), '--json', *args],
        capture_output=True, text=True, timeout=90)
    assert proc.returncode == expected, (proc.returncode, proc.stdout, proc.stderr)
    return json.loads(proc.stdout)

def exercise(project, cwd):
    proc = subprocess.run([sys.executable, '-I', '-c', SCRIPT + CLI_SCRIPT,
        str(project), str(project)], cwd=cwd, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    return proc.stdout.strip().splitlines()

def main():
    OUT.mkdir(exist_ok=True)
    release = release_check.report()
    assert release['result'] == 'PASS', release
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    bundle_files = files_at(ROOT / 'dist')
    version = bundle_files['.claude/ORCHESTRATOR_VERSION'].decode().strip()
    source_files = {'src/' + n: raw for n, raw in files_at(ROOT / 'src').items()}
    for name in bundle_files:
        if name.startswith('tools/'):
            source_files[name] = (ROOT / name).read_bytes()
    for name in ('tools/build_dist.py', 'tools/install.py', 'tools/release_check.py',
                 'tools/generate_workers.py', 'LICENSE'):
        source_files[name] = (ROOT / name).read_bytes()
    bundle_raw, source_raw = archive(bundle_files), archive(source_files)
    bundle_name = f'orchestrator-rc-{digest(bundle_raw)[:16]}.zip'
    source_name = f'orchestrator-source-{digest(source_raw)[:16]}.zip'
    save_once(OUT / bundle_name, bundle_raw)
    save_once(OUT / source_name, source_raw)
    baseline_raw = subprocess.check_output(['git', 'archive', '--format=zip', head, 'dist'], cwd=ROOT)
    checks = {}
    with tempfile.TemporaryDirectory(prefix='orchestrator rc ') as folder:
        temp = Path(folder)
        candidate, source, prior = temp/'candidate', temp/'source', temp/'prior'
        for raw, target in ((bundle_raw, candidate), (source_raw, source), (baseline_raw, prior)):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                z.extractall(target)
        # Pure output planning from the archived inputs, with the frozen stamp.
        # This is a reproducibility check, not a bypass of the checked builder.
        spec = importlib.util.spec_from_file_location('rc_frozen_builder', source/'tools/build_dist.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        planned = {p.relative_to(candidate).as_posix(): s.encode('utf-8')
                   for p,s in builder.planned_files(version, candidate).items()}
        assert planned == bundle_files
        assert archive(bundle_files) == bundle_raw
        checks['reproducible_from_archived_inputs'] = True
        checks['deterministic_archive'] = True
        baseline = prior/'dist'
        baseline_version = (baseline/'.claude/ORCHESTRATOR_VERSION').read_text().strip()
        for mode in ('clean', 'upgrade'):
            project = temp/mode
            project.mkdir()
            (project/'.claude').mkdir()
            (project/'user.txt').write_text('preserve user data\n', encoding='utf-8')
            (project/'CLAUDE.md').write_text('# Consumer instructions\n\nKeep user work.\n', encoding='utf-8')
            (project/'.mcp.json').write_bytes(canonical({'mcpServers': {'user': {'command': 'user-owned'}}}))
            (project/'.claude/settings.json').write_bytes(canonical({'permissions': {'allow': ['Read(user.txt)']}, 'userSetting': True}))
            before_user = {name:(project/name).read_bytes() for name in ('user.txt','.mcp.json')}
            if mode == 'upgrade':
                assert invoke(baseline, 'apply', project)['result'] == 'APPLIED'
            old_owned = {n:(project/n).read_bytes() for n in json.loads((baseline/'bundle-manifest.json').read_text())['files']} if mode == 'upgrade' else {}
            applied = invoke(candidate, 'apply', project)
            assert applied['result'] == 'APPLIED', applied
            assert invoke(candidate, 'plan', project)['result'] == 'NO_CHANGES'
            assert invoke(candidate, 'status', project)['bundle_version'] == version
            manifest = json.loads(bundle_files['bundle-manifest.json'])
            assert all((project/n).read_bytes() == bundle_files[n] for n in manifest['files'])
            checks[mode+'_installed_fake_workflow'] = exercise(project, temp)
            controls = subprocess.run([sys.executable, str(project/'tools/controller_control.py'),
                '--project', str(project), 'status'], capture_output=True, text=True, timeout=30)
            assert controls.returncode == 0, controls.stderr
            assert json.loads(controls.stdout)['paid_work_started'] is False
            assert all((project/n).read_bytes() == raw for n,raw in before_user.items())
            settings = json.loads((project/'.claude/settings.json').read_text())
            assert settings['userSetting'] is True
            assert 'Read(user.txt)' in settings['permissions']['allow']
            assert 'Keep user work.' in (project/'CLAUDE.md').read_text()
            journal = files_at(project/'.claude/task-executor-v2')
            backup = Path(applied['backup_location']).name
            owned = project/'ORCHESTRATOR.md'
            saved = owned.read_bytes()
            owned.write_bytes(saved+b'\nConsumer edit.\n')
            conflict = invoke(candidate, 'rollback', project, '--backup', backup, expected=1)
            assert conflict['result'] == 'CONFLICT'
            assert owned.read_bytes() == saved+b'\nConsumer edit.\n'
            owned.write_bytes(saved)
            invoke(candidate, 'rollback', project, '--backup', backup)
            assert files_at(project/'.claude/task-executor-v2') == journal
            assert all((project/n).read_bytes() == raw for n,raw in before_user.items())
            if mode == 'upgrade':
                assert all((project/n).read_bytes() == raw for n,raw in old_owned.items())
                assert invoke(candidate, 'status', project)['bundle_version'] == baseline_version
                for n in set(manifest['files']) - set(old_owned):
                    assert not (project/n).exists(), n
            else:
                assert not (project/'ORCHESTRATOR.md').exists()
                assert (project/'CLAUDE.md').read_text() == '# Consumer instructions\n\nKeep user work.\n'
            checks[mode+'_install_rollback_preservation_and_drift_rejection'] = True
    assert files_at(ROOT/'dist') == bundle_files, 'bundle changed during verification'
    result = {'schema_version':1,'result':'PASS','candidate_kind':'unpublished-dirty-source-rc',
        'source_head':head,'python_version':sys.version,'bundle_version':version,'baseline_bundle_version':baseline_version,
        'provider_calls':0,'paid_experiment_cost_usd':0,
        'bundle':{'file':bundle_name,'sha256':digest(bundle_raw),'files':{n:digest(v) for n,v in bundle_files.items()}},
        'source_inputs':{'file':source_name,'sha256':digest(source_raw),'files':{n:digest(v) for n,v in source_files.items()}},
        'reproducibility_scope':'Pure bundle assembly from archived inputs; full offline harness runs in the source checkout.',
        'baseline_archive_sha256':digest(baseline_raw),
        'verification_inputs':{n:digest((ROOT/n).read_bytes()) for n in (
            'test/results/2026-10-01-rc-freeze.py',
            'test/harness/worker_executor_consumer_tests.py',
            'test/harness/worker_n8_consumer_tests.py')},
        'checks':checks,'release_check':release,
        'controller_uplift_qualified':False,'publication_ready':False}
    (OUT/'verification.json').write_bytes(canonical(result))
    print(json.dumps({'result':'PASS','bundle':bundle_name,'bundle_sha256':digest(bundle_raw),
        'bundle_files':len(bundle_files),'source_files':len(source_files),'checks':checks},indent=2))

if __name__ == '__main__':
    main()
