from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'src/agrocebada/modeling.py';s=p.read_text(encoding='utf-8')
a=s.index('def legacy_select(');b=s.index('def score_order(',a);s=s[:a]+s[b:]
a=s.index('def train(');s=s[:a]+'''def train(official_only=False):
    from .robust import run
    return run(official_only=official_only)
''';s=s.replace('from scipy.optimize import minimize\n','');p.write_text(s,encoding='utf-8')
p=root/'src/agrocebada/inference.py';s=p.read_text(encoding='utf-8');a=s.index('    def legacy_explain(');b=s.index('    def explain(',a);p.write_text(s[:a]+s[b:],encoding='utf-8')
