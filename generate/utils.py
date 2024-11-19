ANSWER_ONLY_LAST_PROBLEM= "Based on the above examples, answer the following question.\nYou only need to answer the following given question.\n\n"

CODE_INSTRUCTION = """1. Do not include print statements or main functions in your response. Provide answers only in the form of helper functions or subfunctions.
2. Include at least one function named `solution` with no parameters, so I can directly call this function to execute the code.\n\n"""

JAVA_IMPORT = "If it is necessary to import essential packages, please follow this format:\n// First, we import essential packages\nimport java...;\n// Second, we write the solution code\npublic static String solution() {...}\n\n"

CPP_INCLUDE = "You don't need to include any header files and don't need to use 'using namespace std;' as it's already included.\n\n"

import re

def_head = {
    "python": r"^def solution\(\)\s*:",  # Python必须从行首开始
    "r": r"^solution <- function\(\)\s*{",  # R语言从行首开始
    "js": r"^function solution\(\)\s*{",  # JavaScript从行首开始
    "cpp": r"^(\w+\s+)?solution\(\)\s*{",  # C++可能有返回类型
    "java": r"public\s+static\s+(\w+\s+)?solution\(\)\s*{"  # Java可能有访问修饰符和返回类型
}

function_patterns = {
    "python": r"^def (\w+)\(\)\s*:",
    "r": r"^(\w+) <- function\(\)\s*{",
    "js": r"^function (\w+)\(\)\s*{",
    "cpp": r"^\w+ (\w+)\(\)\s*{",
    "java": r"public static \w+ (\w+)\(\)\s*{"
}


def change_head(code, lang):
    if re.search(def_head[lang], code, re.MULTILINE):
        return code, True
    heads = re.findall(function_patterns[lang], code, re.MULTILINE)
    if len(heads) == 1:
        old_head = heads[0]
        code = code.replace(old_head, "solution")
        return code, True
    return code, False


def truncate(code, lang):
    if "```" in code:
        # although there is no ``` in the prompt, outputs generated from instruct version of LLM will have ```
        code_block_pattern = r"```[\w]*\n(.*?)```"
        matches = re.findall(code_block_pattern, code, re.DOTALL)
        if matches:
            # java的会生成一个不正确的，又生成一个正确的，所以还是先用-1的吧
            code = matches[-1].strip()
            code, statue = change_head(code, lang)
            if not statue:
                code = matches[-2].strip()
                code, statue = change_head(code, lang)
    else:
        code, _ = change_head(code, lang)
    return code.strip()
