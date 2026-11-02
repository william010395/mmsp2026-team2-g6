"""Render the recorded buffer sweep with Matplotlib (no network needed)."""
import csv, os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', '/tmp/voicelink-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statistics import mean, stdev
out=Path(__file__).resolve().parents[1]/'docs/results'
rows=list(csv.DictReader((out/'buffer.csv').open()))
xs=list(range(20,201,20))
fig,axes=plt.subplots(3,1,figsize=(9,8),sharex=True,layout='constrained')
for ax,field,label in zip(axes,['concealed','late','avg_delay_ms'],['Concealed frames','Late frames','Arrival-to-play delay (ms)']):
    groups=[[float(r[field]) for r in rows if int(r['buffer_ms'])==x] for x in xs]
    ax.errorbar(xs,[mean(g) for g in groups],yerr=[stdev(g) for g in groups],fmt='o-',capsize=4)
    ax.set_ylabel(label); ax.grid(alpha=.25)
axes[-1].set_xlabel('Target buffer (ms)'); axes[-1].set_xticks(xs)
fig.suptitle('VoiceLink: loss 5%, jitter U(0,30 ms), reorder 5%\n2 s speech excerpt; seed 1; mean ± sample SD, n=3')
for ext in ['svg','png','pdf']:fig.savefig(out/f'buffer.{ext}',dpi=150)
