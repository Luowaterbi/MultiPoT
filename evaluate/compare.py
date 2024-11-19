import json
import os
from collections import Counter, defaultdict
# import numpy as np
import argparse
import pprint
from multiprocessing import Pool, cpu_count
from functools import partial
import time
import tqdm

PATH = "../"
# PATH = "/Users/s1mple/Projects/Self-Learn/"

def get_file_name(dataset, lang, args):
    path = PATH + f"{args.middle_dir}/{dataset}_{lang}_{args.examples}{args.output_suffix}.json"
    return json.load(open(path, "r"))


def evaluate(dataset, langs, args):
    ds = get_file_name(dataset, langs[0], args)
    for lang in langs[1:]:
        cur_ds = get_file_name(dataset, lang, args)
        for d, cd in zip(ds, cur_ds):
            d["exec_ans"].extend(cd["exec_ans"])
            d["code"].extend(cd["code"])
            d["RE"].extend(cd["RE"])
            if "loss" in d:
                d["loss"].extend(cd["loss"])
            if "verfier_loss" in d:
                d["verfier_loss"].extend(cd["verfier_loss"])
    # if len(langs) > 1:
    #     for d in ds:
    #         d["loss"], d["exec_ans"], d["code"] = zip(*sorted(zip(d["loss"], d["exec_ans"], d["code"]), reverse=True))
    ds = calcu_mp(ds, args.opt)
    if args.save:
        # for d in ds:
        #     if not d["passed"] and not d["RE"][0]:
        #         print(d["exec_ans"][0], d["target"])
        if len(langs) == 1:
            save_path = PATH + f"{args.middle_dir}/{dataset}_{langs[0]}_{args.examples}{args.output_suffix}_compare.json"
        else:
            save_path = PATH + f"{args.middle_dir}/{dataset}_multi_{args.examples}{args.output_suffix}_compare.json"
        json.dump(ds, open(save_path, "w"), indent=4)
        # ds = sorted(ds, key=lambda x: x["time"], reverse=True)
        # for d in ds[:3]:
        #     print(d["exec_ans"][0], d["target"], d["time"])

def calcu_mp(ds, opt):
    ds = [calcu(d, opt) for d in ds]
    total = len(ds)
    # res = []
    # for d in pbar:
    #     res.append(calcu(d, opt))
    # ds = res
    correct = sum(d["passed"] for d in ds)
    acc = correct / total
    print(acc)
    # res = sorted(ds, key=lambda x:x["time"], reverse=True)
    # print(json.dumps(res[0], indent=4))
    return ds


def calcu(d, opt):
    # start_time = time.time()
    target = d['target']
    re_ans = []
    d["passed"] = False
    for a, r in zip(d['exec_ans'], d['RE']):
        if r:
            continue
        if isinstance(target, str):
            if target in ["yes", "no"]:
                extract_ans = d["input"].split(" ")[-1][:-1]
                if a.lower() == "true" or a.lower() == "yes" or a == "1" or a == extract_ans:
                    re_ans.append("yes")
                else:
                    re_ans.append("no")
            else:
                re_ans.append(a)
            continue
        else:
            try:
                a2 = float(a)
                if "percent" in d["input"] and a2 < 1:
                    a2 = a2 * 100
                if abs(a2 - target) < 1e-3:
                    re_ans.append(str(target))
                else:
                    re_ans.append(str(round(a2, 3)))
            except:
                re_ans.append(a)
    if opt == "best":
        if str(target) in re_ans:
            d["passed"] = True
    elif opt == "vote":
        c = Counter(re_ans)
        if len(c) == 0:
            return d
        if c.most_common(1)[0][0] == str(target):
            d["passed"] = True
    elif opt == "all":
        if len(re_ans) == len(d['exec_ans']) and len(set(re_ans)) == 1 and str(target) in re_ans:
            d["passed"] = True
    else:
        raise NotImplementedError
    # end_time = time.time()
    # d["time"] = end_time - start_time
    return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", type=str, default="math")
    parser.add_argument("--langs", type=str, default="python")
    parser.add_argument("--examples", type=str, default="fewshot")
    parser.add_argument("--output_suffix", type=str, default="")
    parser.add_argument('--middle_dir', type=str, default='outputs_deepseek')
    parser.add_argument("--multi", action="store_true", default=False)
    parser.add_argument("--opt", type=str, default="vote")
    parser.add_argument("--save", action="store_true", default=False, help="save the result")
    args = parser.parse_args()

    argsdict = vars(args)
    print(pprint.pformat(argsdict))
    datasets = args.datasets.strip().split(",")
    langs = args.langs.strip().split(",")
    
    for dataset in datasets:
        if args.multi:
            evaluate(dataset, langs, args)
        else:
            for lang in langs:
                evaluate(dataset, [lang], args)