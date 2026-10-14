import importlib.util,pathlib,sys,time
root=pathlib.Path(sys.argv[1]);label=sys.argv[2]
script=root/'packages/graft-setup/graft-setup/scripts/fs_probe.py'
sys.path.insert(0,str(script.parent))
spec=importlib.util.spec_from_file_location('load_probe',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
(root/'.graft'/f'kernel5-{label}-armed').write_text(str(time.time()))
deadline=time.monotonic()+180
while not (root/'.graft/kernel5-release').exists():
 if time.monotonic()>deadline:raise TimeoutError('load release not received')
 time.sleep(.05)
sys.argv=[str(script),'--parent',str(root/'.graft'),'--seconds','60','--workers','16','--interval-ms','1','--output',str(root/'.graft'/f'kernel5-{label}-load.json')]
raise SystemExit(module.main())
