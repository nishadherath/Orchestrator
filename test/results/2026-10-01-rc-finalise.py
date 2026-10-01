"""Close the bounded RC only after the saved full harness and archives pass."""
from __future__ import annotations
import dataclasses
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'test/results/2026-10-01-rc'
sys.path.insert(0,str(ROOT/'test/harness'))
import check

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replace(path, old, new):
    text=path.read_text(encoding='utf-8')
    if old in text:
        path.write_text(text.replace(old,new),encoding='utf-8',newline='\n')
    else:
        assert new in text, (path,old)

harness_path=ROOT/'test/results/2026-10-01-rc-final-harness.json'
harness=json.loads(harness_path.read_text(encoding='utf-8-sig'))
assert harness['result']=='PASS' and len(harness['checks'])>=83, harness.get('result')
assert all(row['status']=='PASS' for row in harness['checks'])
v=json.loads((OUT/'verification.json').read_text())
assert v['result']=='PASS' and v['provider_calls']==0
for key in ('bundle','source_inputs'):
    archive=OUT/v[key]['file']
    assert sha(archive)==v[key]['sha256']
    for name,expected in v[key]['files'].items():
        path=(ROOT/'dist'/name) if key=='bundle' else (ROOT/name)
        assert sha(path)==expected, name
count=len(harness['checks'])
result=ROOT/'docs/stage-results/release-candidate-2026-10-01.md'
replace(result,'Exact-bundle verification passed. Final full offline harness is pending.',
    f'Bounded RC verification is complete: the final full offline harness passed {count}/{count}\nchecks, and exact-bundle installation, upgrade and rollback passed.')
replace(result,'| `python test/harness/check.py --json` | Final result pending |',
    f'| `python test/harness/check.py --json` | PASS, {count}/{count} checks on the rebuilt bundle |')
replace(ROOT/'docs/RELEASE-CANDIDATE-2026-10-01.md',
    'Final evidence and disposition will be recorded after verification.',
    'Bounded RC verification is complete. See\n`docs/stage-results/release-candidate-2026-10-01.md` for the exact artefact,\nfinal offline results and publication prerequisites. Controller uplift remains\nan unfinished qualification goal.')
replace(ROOT/'CLAUDE.md',
    'The operator\'s 2026-10-01 direction is to finish the bounded release candidate.',
    'The bounded release candidate verification completed on 2026-10-01. See\n`docs/stage-results/release-candidate-2026-10-01.md` for the result.')
replace(ROOT/'CLAUDE.md',
    'Review shipping changes, correct supported\nclaims, freeze an exact bundle and verify install, upgrade and rollback with\nthe complete offline gate.',
    'The shipping review, corrected supported claims, frozen bundle, installed\nlifecycle checks and full offline gate passed.')
handoff=ROOT/'handoffs/2026-10-01-bounded-rc.md'
replace(handoff,
    'Recorded RC scope, corrected stale documentation, and repaired fail-open build/release provenance checks. No commit made. Final build, frozen-bundle lifecycle checks and full harness remain pending at this checkpoint.',
    f'Recorded RC scope, corrected documentation and repaired build/release provenance. The checked build passed; the frozen 84-file bundle reproduces from 90 source inputs. Clean install, actual-baseline upgrade, rollback, consumer-drift refusal and configuration/task-journal preservation passed. Final full offline harness: {count}/{count} PASS. See `docs/stage-results/release-candidate-2026-10-01.md` and `test/results/2026-10-01-rc/verification.json`. No commit or publication performed.')
replace(handoff,
    'RC readiness must be supported by a new complete offline result and exact artifact hashes, not only prior test counts.',
    'The unpublished RC is verified by the new complete offline result and exact artefact hashes. Clean-source publication still requires the intended source commit, a checked rebuild and explicit publication authority.')
replace(handoff,
    'Complete the focused shipping review, run the checked builder, freeze exact source and bundle bytes, verify installed lifecycle behaviour, and run the complete offline harness. Save the RC disposition with publication prerequisites intact.',
    'Bounded RC work is complete. Read the RC result and preserve its frozen archives. If publication is requested, review and commit intended source changes, rebuild from the clean source commit and verify that newly stamped artefact. Keep Controller uplift unfinished; do not restart paid qualification experiments under the completed RC scope.')
r=check.Report()
check.check_prose(r)
check.check_handoffs(r)
check.check_dist(r)
check.check_release_candidate(r)
rows=[dataclasses.asdict(row) for row in r.checks]
checks_path=ROOT/'test/results/2026-10-01-rc-doc-checks.json'
checks_path.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not r.failed, rows
final={'schema_version':1,'rc_verification_complete':True,'publication_ready':False,
    'full_harness_checks':count,'bundle_sha256':v['bundle']['sha256'],
    'bundle_version':v['bundle_version'],'provider_calls':0,
    'unfinished_qualification_goals':['Controller uplift','general host enforcement','served effort','frontier profile'],
    'publication_actions':v['release_check']['operator_actions'],
    'evidence_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in (
        harness_path,OUT/'verification.json',checks_path,result,handoff,
        ROOT/'test/results/2026-10-01-rc-build.log',Path(__file__).resolve())}}
(OUT/'readiness.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(final,indent=2))
