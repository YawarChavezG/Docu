"""Check GitHub Actions runs."""
import json, subprocess, sys

r = subprocess.run(
    [r"C:\Program Files\GitHub CLI\gh.exe", "api", "repos/YawarChavezG/Docu/actions/runs"],
    capture_output=True, text=True, timeout=15,
    env={**subprocess.os.environ, "GH_TOKEN": "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"}
)

d = json.loads(r.stdout)
for run in d["workflow_runs"][:8]:
    print(f"{run['event']:10} {run['conclusion']:10} {run['head_branch'][:30]:30} {run['created_at'][:19]}")
