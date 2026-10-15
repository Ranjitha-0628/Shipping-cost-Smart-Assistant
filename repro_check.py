import hashlib
import subprocess
import sys


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


hashes = []
for i in range(1, 4):
    out = f"output_run{i}.csv"
    subprocess.run([sys.executable, "run.py", out], check=True)
    hashes.append(file_hash(out))
    print(f"run {i}: {hashes[-1]}")

print("IDENTICAL: all 3 runs match byte for byte" if len(set(hashes)) == 1 else "DIFFERENT: investigate")