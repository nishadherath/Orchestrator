import pathlib,subprocess,sys,time,json,os
r=pathlib.Path('D:/Code/Claude/Orchestrator');out=r/'.graft';logs=[];procs=[]
for label,cmd in [('windows',[sys.executable,str(out/'armed_load5.py'),str(r),'windows']),('linux',['wsl.exe','-d','kali-linux','--cd','/','--exec','/usr/bin/python3','/mnt/d/Code/Claude/Orchestrator/.graft/armed_load5.py','/mnt/d/Code/Claude/Orchestrator','linux'])]:
 log=(out/f'kernel5-{label}-host.log').open('wb');logs.append(log);procs.append(subprocess.Popen(cmd,stdout=log,stderr=log,stdin=subprocess.DEVNULL))
end=time.monotonic()+180
while not all((out/f'kernel5-{label}-armed').exists() for label in ['windows','linux']):
 if time.monotonic()>end:raise TimeoutError('both hosts did not arm')
 time.sleep(.1)
(out/'kernel5-hosts-armed').write_text(str(time.time()))
while not (out/'kernel5-recorder-ready').exists():
 if time.monotonic()>end+180:raise TimeoutError('recorder did not arm')
 time.sleep(.1)
(out/'kernel5-release').write_text(str(time.time()))
env=dict(os.environ,DO_NOT_TRACK='1',GRAFT_API_KEY='',OPENROUTER_API_KEY='',GRAFT_NO_REFRESH='1',GRAFT_FS_ROOT=str(r),GRAFT_FS_TRACE=str(out/'kernel5-node-fs.jsonl'))
start=time.monotonic()
with (out/'kernel5-node.stdout').open('wb') as stdout,(out/'kernel5-node.stderr').open('wb') as stderr:
 command=['C:/nvm4w/nodejs/node.exe','--require',str(out/'fs_timing.cjs'),'C:/nvm4w/nodejs/node_modules/@nanonets/graft/dist/cli.js','--dir',str(r/'graft'),'check','--json',str(r)]
 p=subprocess.Popen(command,stdout=stdout,stderr=stderr,env=env,cwd=r)
 record={'pid':p.pid,'started_unix':time.time(),'deadline':180}
 try:record['exit_code']=p.wait(timeout=180)
 except subprocess.TimeoutExpired:p.kill();p.wait();record['timed_out']=True
 record['elapsed_seconds']=time.monotonic()-start
 (out/'kernel5-node.json').write_text(json.dumps(record,indent=2)+'\n')
for p in procs:p.wait(timeout=200)
for log in logs:log.close()
