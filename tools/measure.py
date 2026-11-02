"""Reproducible real-time UDP buffer sweep and PLC listening samples."""
import csv, json, sys, tempfile, wave
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from run_mock_tests import run_once, read_pcm, sqnr_db
OUT=ROOT/'docs/results'; OUT.mkdir(exist_ok=True)
cfg=SimpleNamespace(send=[str(ROOT/'voicelink'),'send'],recv=[str(ROOT/'voicelink'),'recv'],port=5304,buffer=60)
rows=[]
with tempfile.TemporaryDirectory() as d:
    cfg.wav=str(Path(d)/'clip.wav')
    with wave.open(str(ROOT/'tests/data/aeueo-16kHz.wav')) as w: data=w.readframes(32000)
    with wave.open(cfg.wav,'wb') as w: w.setparams((1,2,16000,0,'NONE','not compressed')); w.writeframes(data)
    cfg.wav_sec=2
    for buffer in range(20,201,20):
        for trial in range(1,4):
            r=run_once(cfg,str(Path(d)/'out.wav'),impair_opts=['--loss','.05','--jitter','30','--reorder','.05'],recv_opts=['--buffer',str(buffer)])
            if r.recv_rc!=0 or r.stats is None: raise RuntimeError(r.recv_err)
            rows.append(dict(trial=trial,**r.stats))
            print(buffer,trial,r.stats['concealed'],flush=True)
    with (OUT/'buffer.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
# Full source for PLC/codec listening and measurements.
cfg.wav=str(ROOT/'tests/data/aeueo-16kHz.wav')
with wave.open(cfg.wav) as w: cfg.wav_sec=w.getnframes()/16000
src=read_pcm(cfg.wav); comparisons=[]
for codec in ['pcm','mulaw']:
    for plc in ['zero','repeat']:
        path=OUT/f'loss5-{codec}-{plc}.wav'
        r=run_once(cfg,str(path),impair_opts=['--loss','.05'],recv_opts=['--plc',plc],send_opts=['--codec',codec])
        if r.recv_rc!=0 or r.stats is None: raise RuntimeError(r.recv_err)
        comparisons.append(dict(codec=codec,plc=plc,sqnr_db=sqnr_db(src,r.pcm),**{'recv':r.stats,'send':r.send_stats}))
(OUT/'plc.json').write_text(json.dumps(comparisons,indent=2)+'\n')
# Burst demonstrates bounded queue and overflow.
r=run_once(cfg,str(OUT/'burst.wav'),send_opts=['--burst'])
if r.recv_rc!=0 or r.stats is None: raise RuntimeError(r.recv_err)
(OUT/'burst.json').write_text(json.dumps(r.stats,indent=2)+'\n')
# Render saved data separately; Matplotlib is optional for core tests.
import subprocess
subprocess.run([sys.executable,str(ROOT/'tools/plot.py')],check=True)
