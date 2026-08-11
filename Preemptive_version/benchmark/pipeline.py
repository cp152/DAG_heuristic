import os
import json
import hashlib
import subprocess
import statistics
from typing import List, Dict, Any, Optional


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run_pipeline(categorys: List[str], familys: List[str], test_loc: str) -> Dict[str, Any]:
    """
    Process index.jsonl, run helper scripts and an external test executable.

    Hardcoded resources (relative to this file's directory):
    - index.jsonl
    - python helper: 1.py (reads a JSON dict from stdin, writes A to stdout)
    - c++-style helper: 2.exe (reads concatenated A+B from stdin, writes numeric C)
    - results directory: results/

    Args:
      categorys: list of category values to match (entry['category'] in categorys)
      familys: list of family values to match (entry['family'] in familys)
      test_loc: path to an executable (.exe) which will be run with input A to produce B

    Returns:
      dict with max/min/mean for C, D, and C/D ratio (and lists of values for debugging)
    """
    base_dir = os.path.dirname(__file__)
    index_path = os.path.join(base_dir, "index.jsonl")
    helper_py = os.path.join(base_dir, "1.py")
    helper_exe = os.path.join(base_dir, "2.exe")
    results_dir = os.path.join(base_dir, "results")

    # check test_loc is an exe file
    if not test_loc.lower().endswith('.exe'):
        raise ValueError('test_loc must be a .exe file')
    if not os.path.isfile(test_loc):
        raise FileNotFoundError(f'test_loc executable not found: {test_loc}')

    if not os.path.isfile(index_path):
        raise FileNotFoundError(f'index.jsonl not found at {index_path}')

    if not os.path.isfile(helper_py):
        raise FileNotFoundError(f'helper python script not found: {helper_py}')
    if not os.path.isfile(helper_exe):
        raise FileNotFoundError(f'helper exe (2.exe) not found: {helper_exe}')

    Cs = []
    Ds = []
    ratios = []

    # try two candidate bases for the json files referenced by index.jsonl
    candidate_bases = [base_dir, os.path.join(base_dir, 'reference_results')]

    with open(index_path, 'r', encoding='utf-8') as idxf:
        for line in idxf:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            if entry.get('category') not in categorys:
                continue
            if entry.get('family') not in familys:
                continue

            rel_path = entry.get('path')
            if not rel_path:
                continue

            json_path: Optional[str] = None
            for b in candidate_bases:
                candidate = os.path.join(b, rel_path)
                if os.path.isfile(candidate):
                    json_path = candidate
                    break
            if json_path is None:
                # could not find the referenced json file; skip
                continue

            # verify sha256
            actual_sha = _sha256_of_file(json_path)
            expected_sha = entry.get('sha256')
            if expected_sha and actual_sha != expected_sha:
                # sha mismatch -> skip
                continue

            # prepare input dictionary for helper 1.py: load the json file content
            with open(json_path, 'r', encoding='utf-8') as jf:
                try:
                    payload = json.load(jf)
                except Exception:
                    payload = {"path": rel_path}

            # call 1.py (python helper) with the dict via stdin
            p1 = subprocess.run(["python", helper_py], input=json.dumps(payload), text=True, capture_output=True)
            if p1.returncode != 0:
                continue
            A = p1.stdout.strip()

            # call the user-provided executable test_loc with A as stdin -> B
            p_test = subprocess.run([test_loc], input=A, text=True, capture_output=True)
            if p_test.returncode != 0:
                continue
            B = p_test.stdout.strip()

            # pass A+B to helper_exe (2.exe) via python invocation (helper_exe is a python script with .exe name)
            combined = A + B
            p2 = subprocess.run(["python", helper_exe], input=combined, text=True, capture_output=True)
            if p2.returncode != 0:
                continue
            C_raw = p2.stdout.strip()
            try:
                C = float(C_raw)
            except Exception:
                continue

            # find results json corresponding to rel_path inside results_dir
            result_path = os.path.join(results_dir, rel_path)
            if not os.path.isfile(result_path):
                continue
            try:
                with open(result_path, 'r', encoding='utf-8') as rf:
                    rj = json.load(rf)
            except Exception:
                continue
            D = rj.get('optimal_makespan')
            try:
                D = float(D)
            except Exception:
                continue

            Cs.append(C)
            Ds.append(D)
            ratios.append(C / D if D != 0 else float('inf'))

    if not Cs:
        print('No valid entries processed')
        return {'max': None, 'min': None, 'mean': None, 'Cs': Cs, 'Ds': Ds, 'ratios': ratios}

    stats = {
        'C_max': max(Cs),
        'C_min': min(Cs),
        'C_mean': statistics.mean(Cs),
        'D_max': max(Ds),
        'D_min': min(Ds),
        'D_mean': statistics.mean(Ds),
        'ratio_max': max(ratios),
        'ratio_min': min(ratios),
        'ratio_mean': statistics.mean(ratios),
        'Cs': Cs,
        'Ds': Ds,
        'ratios': ratios,
    }

    # print concise summary to console
    print('C_max:', stats['C_max'])
    print('C_min:', stats['C_min'])
    print('C_mean:', stats['C_mean'])
    print('ratio_max:', stats['ratio_max'])
    print('ratio_min:', stats['ratio_min'])
    print('ratio_mean:', stats['ratio_mean'])

    return stats


if __name__ == '__main__':
    # quick example: expects three command-line args are not used here — just a convenience runner
    import sys
    print('This module provides run_pipeline(categorys, familys, test_loc)')
