import os
import subprocess
import math
from datetime import datetime
from pathlib import Path
from tqdm import tqdm


def run_command(command):
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, command)
    return completed

def _is_valid_path_string(path_value):
    if not isinstance(path_value, str) or not path_value.strip():
        return False
    if "\x00" in path_value:
        return False
    if os.name == "nt":
        invalid_chars = set('<>:"|?*')
        if any(ch in path_value for ch in invalid_chars):
            return False
    return True


def _validate_existing_file(path_value, label):
    if not _is_valid_path_string(path_value):
        print(f"Error: {label} path is invalid: {path_value!r}")
        return False

    path = Path(path_value)
    if not path.exists():
        print(f"Error: {label} path does not exist: {path_value}")
        return False
    if not path.is_file():
        print(f"Error: {label} path is not a file: {path_value}")
        return False
    return True


def _validate_out_loc(path_value, test_id):
    if not _is_valid_path_string(path_value):
        print(f"Error: test point {test_id} has an invalid out_loc: {path_value!r}")
        return False
    return True


def _resolve_optional_value(case, key, default):
    value = case.get(key)
    if value is None:
        return default
    return value


def test_all(algo_loc = "algo-1.exe", gen_loc = "gen.exe", n = 27, n_t = 9, p = 0.25, times = 10000, out_loc = "data/res1", stop_count = -1):
    fac_n_t = math.factorial(n_t)
    if stop_count == -1:
        stop_count = times

    if stop_count > 50:
        stop_count = 50

    root = Path(out_loc)
    root.mkdir(parents=True, exist_ok=True)

    count = 0

    results = []

    for i in tqdm(range(times), desc="test_all", leave=True):
        count += 1
        infile = root / f"{i}.in"
        pfile = root / f"{i}.p"
        alt_pfile = root / f"all-{i}.p"
        outfile = root / f"{i}.out"
        ansfile = root / f"{i}.ans"
        # if(i%10 == 0):
        #     print(f"Running test {i}...")

        run_command(["gens/" + gen_loc, str(n), str(n_t), str(p), str(infile)])
        run_command(["all.exe", str(infile), str(alt_pfile)])
        run_command(["algos/" + algo_loc, str(infile), str(pfile)])
        run_command(["sol.exe", str(infile), str(pfile), str(outfile), "1"])
        run_command(["sol.exe", str(infile), str(alt_pfile), str(ansfile), str(fac_n_t)])

        with ansfile.open("r", encoding="utf-8") as f:
            ans_values = [int(x) for x in f.read().split() if x.strip()]
        if not ans_values:
            raise ValueError(f"Empty answer file: {ansfile}")
        ans = min(ans_values)

        with outfile.open("r", encoding="utf-8") as f:
            out_values = [int(x) for x in f.read().split() if x.strip()]
        if not out_values:
            raise ValueError(f"Empty output file: {outfile}")
        out = out_values[0]

        ratio = out / ans if ans != 0 else float("inf")

        if(ratio < 1):
            print(f"Error: out < ans for test {i}: out={out}, ans={ans}")

        if(out == ans):
            #删除本次测试的数据
            infile.unlink(missing_ok=True)
            pfile.unlink(missing_ok=True)
            alt_pfile.unlink(missing_ok=True)
            outfile.unlink(missing_ok=True)
            ansfile.unlink(missing_ok=True)
            continue

        results.append((i, out, ans, ratio))
        # print(f"{i}: out={out}, ans={ans}, ratio={ratio:.6f}")
        if(len(results) >= stop_count):
            break

    if results:
        ratios = [r for (_, _, _, r) in results]
        outs = [o for (_, o, _, _) in results]
        answers = [a for (_, _, a, _) in results]

        print("\nSummary:")
        print(f"count = {len(results)}")
        print(f"error ratio = {len(results)} / {count} = {len(results)/count}")
        print(f"out avg = {sum(outs) / len(outs):.6f}")
        print(f"ans avg = {sum(answers) / len(answers):.6f}")
        print(f"ratio avg = {sum(ratios) / len(ratios):.6f}")
        print(f"ratio min = {min(ratios):.6f}")
        print(f"ratio max = {max(ratios):.6f}")
        #将以上结果写入root文件夹中的summary文件
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = "summary-" + timestamp + "-" + algo_loc[:-4] + "-" + gen_loc[:-4] + "-n=" + str(n) + "-n_t=" + str(n_t) + "-p=" + str(p)
        with open(root / filename, "w") as f:
            f.write(filename)
            f.write("\n")
            f.write(f"count = {len(results)}\n")
            f.write(f"error ratio = {len(results)} / {count} = {len(results)/count:.6f}\n")
            f.write(f"out avg = {sum(outs) / len(outs):.6f}\n")
            f.write(f"ans avg = {sum(answers) / len(answers):.6f}\n")
            f.write(f"ratio avg = {sum(ratios) / len(ratios):.6f}\n")
            f.write(f"ratio min = {min(ratios):.6f}\n")
            f.write(f"ratio max = {max(ratios):.6f}\n")

def comp(algo1_loc = "algo-1.exe", algo2_loc = "algo-2.exe", gen_loc = "gen.exe", n = 30000, n_t = 10000, p = 0.09, times = 20, out_loc = "data/res1"):
    root = Path(out_loc)
    root.mkdir(parents=True, exist_ok=True)

    results = []

    for i in tqdm(range(times), desc="comp", leave=True):
        infile = root / f"{i}.in"
        pfile1 = root / f"{i}-1.p"
        pfile2 = root / f"{i}-2.p"
        outfile1 = root / f"{i}-1.out"
        outfile2 = root / f"{i}-2.out"
        # if(i%10 == 0):
        #     print(f"Running test {i}...")

        run_command(["gens/" + gen_loc, str(n), str(n_t), str(p), str(infile)])
        run_command(["algos/" + algo1_loc, str(infile), str(pfile1)])
        run_command(["algos/" + algo2_loc, str(infile), str(pfile2)])
        run_command(["sol.exe", str(infile), str(pfile1), str(outfile1), "1"])
        run_command(["sol.exe", str(infile), str(pfile2), str(outfile2), "1"])

        with outfile1.open("r", encoding="utf-8") as f:
            out_values1 = [int(x) for x in f.read().split() if x.strip()]
        if not out_values1:
            raise ValueError(f"Empty output file: {outfile1}")
        out1 = out_values1[0]

        with outfile2.open("r", encoding="utf-8") as f:
            out_values2 = [int(x) for x in f.read().split() if x.strip()]
        if not out_values2:
            raise ValueError(f"Empty output file: {outfile2}")
        out2 = out_values2[0]

        if(out1 == 0 or out2 == 0):
            print(f"Error: out1 or out2 is zero for test {i}: out1={out1}, out2={out2}")
            break

        ratio = out1 / out2 if out2 != 0 else float("inf")

        results.append((i, out1, out2, ratio))
        # print(f"{i}: out1={out1}, out2={out2}, ratio={ratio:.6f}")
        #删除本次测试的数据
        infile.unlink(missing_ok=True)
        pfile1.unlink(missing_ok=True)
        pfile2.unlink(missing_ok=True)
        outfile1.unlink(missing_ok=True)
        outfile2.unlink(missing_ok=True)

    if results:
        ratios = [r for (_, _, _, r) in results]
        outs = [o for (_, o, _, _) in results]
        answers = [a for (_, _, a, _) in results]

        print("\nSummary:")
        print(f"count = {len(results)}")
        print(f"out1 avg = {sum(outs) / len(outs):.6f}")
        print(f"out2 avg = {sum(answers) / len(answers):.6f}")
        print(f"ratio avg = {sum(ratios) / len(ratios):.6f}")
        print(f"ratio min = {min(ratios):.6f}")
        print(f"ratio max = {max(ratios):.6f}")
        #将以上结果写入root文件夹中的summary文件
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = "summary-" + timestamp + "-" + algo1_loc[:-4] + "-" + algo2_loc[:-4] + "-" + gen_loc[:-4] + "-n=" + str(n) + "-n_t=" + str(n_t) + "-p=" + str(p)
        with open(root / filename, "w") as f:
            f.write(filename)
            f.write("\n")
            f.write(f"count = {len(results)}\n")
            f.write(f"out1 avg = {sum(outs) / len(outs):.6f}\n")
            f.write(f"out2 avg = {sum(answers) / len(answers):.6f}\n")
            f.write(f"ratio avg = {sum(ratios) / len(ratios):.6f}\n")
            f.write(f"ratio min = {min(ratios):.6f}\n")
            f.write(f"ratio max = {max(ratios):.6f}\n")

def main(test_cases=None):
    for case in tqdm(test_cases, desc="main", leave=True):
        if not isinstance(case, dict):
            print(f"Error: invalid test case format: {case!r}; skipping")
            continue

        test_id = case.get("id")
        if test_id is None:
            print("Error: missing id; skipping test point")
            continue

        test_type = _resolve_optional_value(case, "type", None)
        algo1 = _resolve_optional_value(case, "algo1", None)
        if not isinstance(test_type, str) or not test_type.strip():
            print(f"Error: test point {test_id} missing type; skipping")
            continue
        if not isinstance(algo1, str) or not algo1.strip():
            print(f"Error: test point {test_id} missing algo1; skipping")
            continue

        if test_type not in {"all", "comp"}:
            print(f"Error: test point {test_id} has unsupported type '{test_type}'; skipping")
            continue

        if test_type == "comp":
            algo2 = _resolve_optional_value(case, "algo2", None)
            if not isinstance(algo2, str) or not algo2.strip():
                print(f"Error: test point {test_id} missing algo2; skipping")
                continue

        gen_loc = _resolve_optional_value(case, "gen", "gen.exe")
        if not _validate_existing_file("gens/" + gen_loc, "gen"):
            print(f"Error: test point {test_id} skipped because gen path is invalid")
            continue

        if not _validate_existing_file("algos/" + algo1, "algo1"):
            print(f"Error: test point {test_id} skipped because algo1 path is invalid")
            continue

        if test_type == "comp" and not _validate_existing_file("algos/" + algo2, "algo2"):
            print(f"Error: test point {test_id} skipped because algo2 path is invalid")
            continue

        if test_type == "all":
            stop_count = _resolve_optional_value(case, "stop_count", -1)
        n = _resolve_optional_value(case, "n", 27 if test_type == "all" else 30000)
        n_t = _resolve_optional_value(case, "n_t", 9 if test_type == "all" else 10000)
        p = _resolve_optional_value(case, "p", 0.25 if test_type == "all" else 0.09)
        times = _resolve_optional_value(case, "times", 10000 if test_type == "all" else 20)
        out_loc = _resolve_optional_value(case, "out_loc", f"data/res{test_id}")

        if not _validate_out_loc(out_loc, test_id):
            print(f"Error: test point {test_id} skipped because out_loc is invalid")
            continue

        if test_type == "all":
            test_all(algo_loc=algo1, gen_loc=gen_loc, n=n, n_t=n_t, p=p, times=times, out_loc=out_loc, stop_count=stop_count)
        else:
            comp(algo1_loc=algo1, algo2_loc=algo2, gen_loc=gen_loc, n=n, n_t=n_t, p=p, times=times, out_loc=out_loc)

test_cases = [
    
        # {
        #     "id": 1,
        #     "type": "all",
        #     "stop_count": 10,
        #     "algo1": "algo-1.exe",
        #     "gen": "gen2.exe",
        #     "n": 27,
        #     "n_t": 9,
        #     "p": 0.25,
        #     "times": 10000,
        #     # "out_loc": f"data/res1"
        # },
    

        # {
        #     "id": 2,
        #     "type": "comp",
        #     "algo1": "algo-1.exe",
        #     "algo2": "algo-2.exe",
        #     "gen": "gen2.exe",
        #     "n": 3000,
        #     "n_t": 1000,
        #     "p": 0.15,
        #     "times": 20,
        #     # "out_loc": f"data/res2"
        # },
        # {
        #     "id": 3,
        #     "type": "comp",
        #     "algo1": "algo-1.exe",
        #     "algo2": "algo-3.exe",
        #     "gen": "gen2.exe",
        #     "n": 3000,
        #     "n_t": 1000,
        #     "p": 0.15,
        #     "times": 20,
        # },
        # {
        #     "id": 4,
        #     "type": "comp",
        #     "algo1": "algo-1.exe",
        #     "algo2": "algo-4.exe",
        #     "gen": "gen2.exe",
        #     "n": 3000,
        #     "n_t": 1000,
        #     "p": 0.15,
        #     "times": 20,
        # },


        # {
        #     "id": 5,
        #     "type": "comp",
        #     "algo1": "algo-0.exe",
        #     "algo2": "algo-1.exe",
        #     "gen": "gen2.exe",
        #     "n": 3000,
        #     "n_t": 1000,
        #     "p": 0.15,
        #     "times": 1000,
        # },


        {
            "id": 6,
            "type": "comp",
            "algo1": "algo-1.exe",
            "algo2": "algo-2.exe",
            "gen": "gen3.exe",
            "n": 3000,
            "n_t": 1000,
            "p": 0.15,
            "times": 1000,
        },
        {
            "id": 7,
            "type": "comp",
            "algo1": "algo-1.exe",
            "algo2": "algo-3.exe",
            "gen": "gen3.exe",
            "n": 3000,
            "n_t": 1000,
            "p": 0.15,
            "times": 1000,
        },
        {
            "id": 8,
            "type": "comp",
            "algo1": "algo-1.exe",
            "algo2": "algo-4.exe",
            "gen": "gen3.exe",
            "n": 3000,
            "n_t": 1000,
            "p": 0.15,
            "times": 1000,
        },
        {
            "id": 9,
            "type": "comp",
            "algo1": "algo-1.exe",
            "algo2": "random.exe",
            "gen": "gen3.exe",
            "n": 3000,
            "n_t": 1000,
            "p": 0.15,
            "times": 1000,
        },
    ]

if __name__ == "__main__":
    main(test_cases=test_cases)