import os

keywords = ['reinforce', 'q_learning', 'qlearning', 'policy', 'reward', 'gym', 'trading_env', 'agent', 'backtest', 'model', 'predict', 'rl_']
found = []

for root, dirs, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or '.venv' in root:
        continue
    for file in files:
        if file.endswith(('.py', '.ipynb', '.md', '.txt', '.yaml', '.json')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    matched = [k for k in keywords if k in content]
                    if matched:
                        found.append((path, matched))
            except Exception:
                pass

print(f"Total matching files: {len(found)}")
for p, m in found[:30]:
    print(f"{p}: {m}")
