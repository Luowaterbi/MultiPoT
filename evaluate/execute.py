import subprocess
from multiprocessing import Pool, cpu_count
import json
from functools import partial
import tqdm
import os
import argparse
from utils import *
from compare import calcu_mp


PATH = "../"


def exec(d, output_path, lang):
    exec_prefix = CODE_PREFIX[lang]
    exec_suffix = CODE_SUFFIX[lang]
    idx = d["exec_idx"]
    save_path = output_path + f"/{idx}"
    if len(d["code"]) == 0:
        d["exec_ans"] = "No code"
    d["exec_ans"] = []
    d["RE"] = []
    for code in d["code"]:
        try:
            code = delete_output(code, lang)
            if lang == "java":
                java_import, code = javaprocess(code)
                exec_prefix = java_import + "\n" + exec_prefix
            if lang == "cpp":
                code = cppprocess(code)
            if len(code) > 2040:
                d["exec_ans"].append("Code too long")
                d["RE"].append(True)
                continue
            code = exec_prefix + "\n" + code + "\n" + exec_suffix
            with open(save_path + FILE_EXTENSIONS[lang], "w") as f:
                f.write(code)
            args = EXECUTE_COMMANDS[lang].format_map(dict(script_name=save_path)).split()
            exec_proc = subprocess.run(args, capture_output=True, text=True, timeout=10)
            # print(f"{idx}:\n {args}\n{code}\n{exec_proc}")
            if exec_proc.returncode == 0:
                ans = exec_proc.stdout.strip()
                if lang in ["cpp", "rust"]:
                    exec_proc = subprocess.run([save_path], capture_output=True, text=True, timeout=10)
                    if exec_proc.returncode == 0:
                        ans = exec_proc.stdout.strip()
                    else:
                        d["exec_ans"].append(exec_proc.stderr)
                        d["RE"].append(True)
                        continue
                elif lang == "ts":
                    exec_proc = subprocess.run(["node", save_path + ".js"], capture_output=True, text=True, timeout=10)
                    if exec_proc.returncode == 0:
                        ans = exec_proc.stdout.strip()
                    else:
                        d["exec_ans"].append(exec_proc.stderr)
                        d["RE"].append(True)
                        continue
                # ans = float(ans)
                # if abs(ans - round(ans)) < 1e-3:
                #     ans = round(ans)
                # d["exec_ans"].append(float(ans))
                d["exec_ans"].append(ans)
                d["RE"].append(False)
            else:
                d["exec_ans"].append(exec_proc.stderr)
                d["RE"].append(True)
        except Exception as e:
            d["exec_ans"].append(str(e))
            d["RE"].append(True)
    return d


def extract_answer(ds):
    trigger = "So the answer is"
    for d in ds:
        d["exec_ans"] = []
        d["RE"] = []
        for code in d["code"]:
            try:
                # 输出很多的，只要开头的这一块
                ans = code.split(trigger)[-1]
                if ans[-1] == ".":
                    ans = ans[:-1]
                # num = num.replace(",", "").replace("$", "").replace("€", "").strip()
                # if num[-1] == "%":
                #     num = float(num[:-1]) / 100
                # else:
                #     num = eval(num)
                d["exec_ans"].append(ans.strip())
                d["RE"].append(False)
            except Exception as e:
                d["exec_ans"].append(str(e))
                d["RE"].append(True)
    return ds


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", type=str, default="gsm")
    parser.add_argument("--langs", type=str, default="")
    parser.add_argument("--output_suffix", type=str, default="")
    parser.add_argument('--middle_dir', type=str, default="")
    parser.add_argument("--examples", type=str, default="fewshot")
    parser.add_argument("--num_cpus", type=int, default=0)
    args = parser.parse_args()

    datasets = args.datasets.strip().split(",")
    langs = args.langs.strip().split(",")
    num_cpus = cpu_count() if args.num_cpus == 0 else args.num_cpus
    
    for dataset in datasets:
        for lang in langs:
            outputs = []
            output_file = f"{dataset}_{lang}_{args.examples}{"_" + args.output_suffix if args.output_suffix else ''}"
            ds = json.load(open(PATH + f"{args.middle_dir}/{output_file}.json", "r"))

            if lang == "cot":
                ds = extract_answer(ds)
                res = calcu_mp(ds, "best")
            else:
                exec_path = PATH + f"execution/{args.middle_dir}/{output_file}"
                if not os.path.exists(exec_path):
                    os.makedirs(exec_path)
                for i, d in enumerate(ds):
                    d["exec_idx"] = i
                exec_lang = partial(exec, output_path=exec_path, lang=lang)
                pbar = tqdm.tqdm(ds, total=len(ds))
                with Pool(num_cpus) as p:
                    ds = list(p.imap(exec_lang, pbar))
                res = calcu_mp(ds, "best")
            json.dump(res, open(PATH + f"{args.middle_dir}/{output_file}_ans.json", "w"), indent=4)