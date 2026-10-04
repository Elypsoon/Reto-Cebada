import json
import re
from agrocebada.common import ROOT,ARTIFACTS,write_json
r=json.loads((ARTIFACTS/"validation.json").read_text(encoding="utf-8"))
final=r["final_selection"]
values={"RMSE":f"{r['metrics']['selected']['rmse']:.3f}","MAE":f"{r['metrics']['selected']['mae']:.3f}","R2":f"{r['metrics']['selected']['r2']:.3f}","OFFICIAL_RMSE":f"{r['metrics']['official']['rmse']:.3f}","BASELINE_RMSE":f"{r['metrics']['regional_mean']['rmse']:.3f}","FINAL_MODELS":"/".join(c['family'] for c in final['candidates']),"STRATEGY":final['strategy'],"FINAL_SOURCES":"/".join(sorted(set(s for c in final['candidates'] for s in c['sources']))) or "ninguna, únicamente datos del reto","COVERAGE":f"{r['interval']['coverage']:.1%}","WIDTH":f"{r['interval']['mean_width']:.3f}","INTERVAL_AVAILABLE":"sí" if r['interval']['available'] else "no","MINUTES":f"{r['seconds']/60:.2f}","MEMORY":f"{r['peak_observed_rss_mb']:.1f}"}
for state in ['Hidalgo','Puebla','Tlaxcala']:values[state.upper()+"_RMSE"]=f"{r['by_state'][state]['rmse']:.3f}"
values["BASELINE_COMPARISON"]=("El procedimiento revisado redujo el RMSE frente a la media regional en esta evaluación." if r['metrics']['selected']['rmse']<r['metrics']['regional_mean']['rmse'] else "El procedimiento revisado todavía no redujo el RMSE frente a la media regional.")
team=json.loads((ROOT/"docs/team-contributions.json").read_text(encoding="utf-8"))
values["TEAM_CONTRIBUTIONS"]="\n\n".join("**"+m["name"]+"**: "+m["contributions"] for m in team["members"])
text=(ROOT/"docs/technical-report.template.md").read_text(encoding="utf-8")
for k,v in values.items():text=text.replace("__"+k+"__",v)
assert not re.search(r"__[A-Z_]+__",text)
sections=dict(re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)",text,re.M|re.S))
counts={k:len(re.findall(r"\S+",v)) for k,v in sections.items()}
limits={"Introducción":(400,550),"Justificación":(100,200),"Objetivos":(1,200),"Metodología":(600,700),"Resultados y discusión":(1,800),"Uso de la ciencia de datos en la inclusión financiera del sector agro":(1,300),"Conclusiones":(1,400)}
for name,(minimum,maximum) in limits.items():assert minimum<=counts[name]<=maximum,(name,counts[name],minimum,maximum)
bibliography=(ROOT/"docs/ai-tools-and-bibliography.md").read_text(encoding="utf-8")
text=text.replace("Véase `ai-tools-and-bibliography.md` para fuentes primarias, documentación de versiones, atribución de skills y registro de herramientas/prompts de IA. Incorporar esas referencias al formato final de entrega.",bibliography.replace("# Fuentes y registro de asistencia de IA\n","",1))
(ROOT/"docs/technical-report.md").write_text(text,encoding="utf-8")
write_json(ARTIFACTS/"technical-report-check.json",{"words":counts,"body_limits_met":True,"results_from_validation":True,"team_contributions":team,"annex_plan":"dos páginas; verificación de PDF registrada por build_report_pdfs.py"})
print(counts,flush=True)
