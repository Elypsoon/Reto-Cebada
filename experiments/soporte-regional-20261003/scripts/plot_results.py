"""Figura de resultados derivados del índice, sin decidir variantes con OOF."""
from pathlib import Path
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
d=pd.read_csv(root/'registry/summary.csv');d=d[d.status.eq('completed')&d.scheme.isin(['principal-5','balanceado-4','rotado-45-5'])&~d.experiment.str.startswith('H')]
d=d[d.route.eq('official')|(d.experiment.eq('E08')&d.route.eq('selected'))].copy()
d['label']=d.experiment
d.loc[d.run_id.str.contains('E07-'),'label']=d.loc[d.run_id.str.contains('E07-'),'run_id'].map(lambda s:'E07 mensual' if 'monthly' in s else 'E07 Whittaker')
d.loc[d.route.eq('selected'),'label']='E08 enriquecido'
order=['E00','E01a','E01b','E02','E03','E04a','E04b','E05','E06','E07 mensual','E07 Whittaker','E08','E08 enriquecido'];labels=[x for x in order if x in set(d.label)]
fig,axes=plt.subplots(1,3,figsize=(15,7),sharey=True)
for ax,scheme,title in zip(axes,['principal-5','balanceado-4','rotado-45-5'],['Principal','Balanceado','Rotado 45°']):
    z=d[d.scheme.eq(scheme)].set_index('label').reindex(labels);y=np.arange(len(labels));colors=['#28634b' if s.startswith('E08') else '#426f99' if s!='E00' else '#727b86' for s in labels]
    ax.barh(y,z.rmse,color=colors,height=.65)
    reference=float(z.loc['E00','regional_rmse']);ax.axvline(reference,color='#aa642d',ls='--',lw=1.5,label=f'Media regional {reference:.3f}')
    ax.set_title(title,fontweight='bold');ax.set_xlabel('RMSE (t/ha)');ax.set_yticks(y,labels);ax.invert_yaxis();ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    for yi,value in zip(y,z.rmse):ax.text(value+.007,yi,f'{value:.3f}',va='center',fontsize=8)
    ax.set_xlim(0,max(1.05,float(z.rmse.max())+.09));ax.legend(loc='lower right',fontsize=8)
fig.suptitle('Experimentos parcelarios · campaña 2025',fontsize=17,fontweight='bold')
fig.text(.5,.02,'Mismas 138 etiquetas en los tres esquemas. E07: configuraciones fijas separadas. E08: composición previa; elegibilidad separada de activación.',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.05,1,.94]);(root/'docs/figures').mkdir(exist_ok=True)
for suffix in ['png','svg']:fig.savefig(root/f'docs/figures/experiment-rmse.{suffix}',dpi=180,bbox_inches='tight')
print(root/'docs/figures/experiment-rmse.png')
