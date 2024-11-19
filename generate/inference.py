import argparse
import pprint
import sys
import os
import re
from tqdm import tqdm
import torch
from vllm import LLM
from vllm import SamplingParams
import json
from utils import *
from math import ceil
import os
import random

# PATH = "/home/work/aigc-user-workspace/luoxianzhen/MultiPoT/"
PATH = "../"


if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

try:
    if torch.backends.mps.is_available():
        device = "mps"
except:
    pass


def read_problems(input_path, output_path):
    outputs = []
    already = []
    if os.path.exists(output_path):    
        outputs = json.load(open(output_path, "r"))
        already = [d["input"] for d in outputs]
    inputs = []
    f = open(input_path, "r")
    for d in f.readlines():
        d = json.loads(d)
        if d["input"] in already:
            continue
        else:
            d["code"] = []
            # d["loss"] = []
            d["ori"] = []
            inputs.append(d)
    return inputs, outputs


def encode_prompt(batch, example="fewshot", lang="python", dataset="math"):
    prompt_batch = []
    prompts = json.load(open("prompts.json"))
    if dataset in ["MWP", "gsm", "asdiv", "svamp"]:
        dataset = "math"
    for i in batch:
        prompt = "Question: " + i["input"] + prompts["instruction"][dataset][lang]
        if lang != "cot":
            prompt += CODE_INSTRUCTION
            if lang == "java":
                prompt += JAVA_IMPORT
            if lang == "cpp":
                prompt += CPP_INCLUDE
        if example == "fewshot":
            prompt = prompts[example][dataset][lang] + ANSWER_ONLY_LAST_PROBLEM + prompt
        prompt_batch.append(prompt)
    
    for i, p in enumerate(random.choices(prompt_batch, k=3)):
        print(f"Prompt Example {i}:\n{p}\n\n")
    return prompt_batch


def generate(dataset, lang, llm, sampling_params, args):
    input_path = PATH + "datasets/" + dataset + ".jsonl"
    print("Input Path:", input_path)
    output_path = PATH + f"{args.middle_dir}/{dataset}_{lang}_{args.examples}{args.output_suffix}.json"
    
    ds, outputs = read_problems(input_path, output_path)
    print("Number of samples in {} need to generate: {}".format(dataset, len(ds)))
    
    for i in tqdm(range(0, len(ds), args.batch_size)):
        batch = ds[i : i + args.batch_size]
        prompts = encode_prompt(batch, example=args.examples, lang=lang, dataset=dataset)
        
        if args.decoding_style == 'sampling':
            loops = ceil(args.N / args.num_seqs_per_iter)
        else:
            loops = 1
        
        for _ in range(loops):
            if "instruct" in args.model.lower() or "chat" in args.model.lower():
                prompts = [[{"role":"user", "content":p}] for p in prompts]
                completions = llm.chat(prompts, sampling_params)
            else:
                completions = llm.generate(prompts, sampling_params)
            for d, completion in zip(batch, completions):  
                gen_seqs = [completion.outputs[i].text for i in range(args.num_seqs_per_iter)]
                # loss_seqs = [completion.outputs[i].cumulative_logprob for i in range(args.num_seqs_per_iter)]
                if gen_seqs is not None:
                    # for gen_seq, loss in zip(gen_seqs, loss_seqs):
                    #     d["code"].append(truncate(gen_seq.strip()))
                    #     d["ori"].append(gen_seq.strip())
                    #     d["loss"].append(loss)
                    #     if len(d["code"]) >= args.N:
                    #         d["code"] = d["code"][:args.N]
                    #         d["loss"] = d["loss"][:args.N]
                    #         d["ori"] = d["ori"][:args.N]
                    #         break
                    for gen_seq in gen_seqs:
                        d["code"].append(truncate(gen_seq.strip(), lang))
                        d["ori"].append(gen_seq.strip())
                        if len(d["code"]) >= args.N:
                            d["code"] = d["code"][:args.N]
                            d["ori"] = d["ori"][:args.N]
                            break

        outputs.extend(batch)
        json.dump(outputs, open(output_path, "w"), indent=4)
    for i, d in enumerate(random.choices(outputs, k=3)):
        print(f"Output Example {i}:\n{d}\n\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='bigcode/starcoder', help="")
    parser.add_argument("--datasets", type=str, default="gsm,asdiv,svamp,math")
    parser.add_argument('--examples', type=str, default="fewshot", choices=["fewshot", "zeroshot"])
    parser.add_argument('--lang', type=str, default="python,r,java,javascript,cpp,cot")
    parser.add_argument('--temperature', type=float, default=0, help="")
    parser.add_argument('--N', type=int, default=1, help="")
    parser.add_argument('--max_len', type=int, default=2048, help="")
    parser.add_argument('--num_gpus', type=int, default=8, help="")
    parser.add_argument('--decoding_style', type=str, default='sampling', help="")
    parser.add_argument('--num_seqs_per_iter', type=int, default=1, help='')
    parser.add_argument('--batch_size', type=int, default=1, help='')
    parser.add_argument('--output_suffix', type=str, default="", help='')
    parser.add_argument('--top_p', type=float, default=1, help="")
    parser.add_argument('--middle_dir', type=str, default='')
    args = parser.parse_args()

    argsdict = vars(args)
    print(pprint.pformat(argsdict))

    os.makedirs(PATH + args.middle_dir, exist_ok=True)

    os.environ['VLLM_WORKER_MULTIPROC_METHOD']="spawn"
    llm = LLM(model=args.model, tensor_parallel_size=args.num_gpus, trust_remote_code=True)
    sampling_params = SamplingParams(n=args.num_seqs_per_iter, temperature=args.temperature, top_p=args.top_p, max_tokens=args.max_len, stop=["Question:"])

    datasets = args.datasets.strip().split(",")
    langs = args.lang.strip().split(",")
    print("datasets:", datasets)
    print("langs:", langs)
    for dataset in datasets:
        for lang in langs:
            print(f"start {dataset} {lang} {args.decoding_style} {args.output_suffix}")
            generate(dataset, lang, llm, sampling_params, args)
            print(f"{dataset} {lang} is done ~")
