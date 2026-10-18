import numpy as np
from .common import ID,TARGET,SCHEMES
from .modeling import original


def eligibility(frames,active_frames,new_information=False,verified=False,control_verified=False):
    ratios={};active_ratios={};failures=[];invalid=[]
    for scheme in SCHEMES:
        candidate=frames.get(scheme);active=active_frames.get(scheme)
        if candidate is None or active is None:invalid.append(scheme);continue
        a=candidate.set_index(ID).sort_index();b=active.set_index(ID).sort_index()
        if len(a)!=138 or not a.index.is_unique or not a.index.equals(b.index) or not np.array_equal(a[TARGET],b[TARGET]) or not np.array_equal(a.spatial_group,b.spatial_group):
            invalid.append(scheme);continue
        if not np.isfinite(a[['prediction','regional_mean',TARGET]]).all().all() or not np.isfinite(b.selected).all():invalid.append(scheme);continue
        rmse=original.metric(a[TARGET],a.prediction)['rmse'];baseline=original.metric(a[TARGET],a.regional_mean)['rmse'];active_rmse=original.metric(b[TARGET],b.selected)['rmse']
        ratios[scheme]=rmse/baseline if baseline else float('inf');active_ratios[scheme]=rmse/active_rmse if active_rmse else float('inf')
        for state,g in a.groupby('Estado'):
            mae=original.metric(g[TARGET],g.prediction)['mae'];reference=original.metric(g[TARGET],g.regional_mean)['mae']
            if len(g)>=10 and mae>1.1*reference+1e-12:failures.append({'scheme':scheme,'state':state,'n':len(g),'mae':mae,'reference_mae':reference})
    checks={'three_schemes':len(ratios)==3 and not invalid,'principal_regional_2pct':ratios.get(SCHEMES[0],np.inf)<=.98,
            'two_schemes_2pct':sum(x<=.98 for x in ratios.values())>=2,'mean_ratio_098':len(ratios)==3 and np.mean(list(ratios.values()))<=.98,
            'max_ratio_105':len(ratios)==3 and max(ratios.values())<=1.05,'state_protection':not failures,
            'principal_active_2pct':active_ratios.get(SCHEMES[0],np.inf)<=.98,'max_active_ratio_105':len(active_ratios)==3 and max(active_ratios.values())<=1.05,
            'new_information':bool(new_information),'verified':bool(verified),'control_verified':bool(control_verified)}
    return {'eligible':bool(all(checks.values())),'checks':{k:bool(v) for k,v in checks.items()},
            'regional_ratios':{k:float(v) if np.isfinite(v) else None for k,v in ratios.items()},'active_ratios':{k:float(v) if np.isfinite(v) else None for k,v in active_ratios.items()},
            'state_failures':failures,'invalid_schemes':invalid,'activated':False,'deployed':False,'sent':False,'interval_available':False,
            'evidence':'Desarrollo sobre las mismas 138 etiquetas; sin campaña independiente.'}
