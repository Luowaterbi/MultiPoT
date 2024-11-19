PROMPT = {
    'pot': "Let's use {lang} to solve math problems.",
    'cot': "Let's think step by step to solve math problems.",
    'translate': "Translate {source} to {target}.",
    'explain': "Provide a concise natural language description of the code and perform the calculations.",
    'fix': "Fix the wrong solution.",
    'sft': '''Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n\n{instruction}\n\n### Response:'''
}

LANGS_MAP = {
    "bash": "Bash",
    "cpp": "C++",
    "go": "Go",
    "java": "Java",
    "js": "JavaScript",
    "php": "PHP",
    "python": "Python",
    "r": "R",
    "rust": "Rust",
    "ts": "TypeScript",
    "cot": "Calculations"
}


CODE_PREFIX = {
    # 'bash': "#!/bin/bash\n\n",
    # 'c#': "using System;\n\nclass Program {\n    ",
    'cpp': "#include <bits/stdc++.h>\n\nusing namespace std;\n\n",
    # 'go': "package main\n\nimport \"fmt\"\n\n",
    'java': "public class Main {\n    public static void main(String[] args) {\n        System.out.println(solution());\n    }\n",
    'js': "",
    # 'php': "<?php\n\n",
    'python': "",
    'r': "",
    # 'rust': "fn main() {\n    ",
    # 'ts': ""
}

CODE_SUFFIX = {
    # 'bash': "\necho $(solution)\n",
    # 'c#': "\n    static void Main() {\n        Console.WriteLine(Solution());\n    }\n}",
    'cpp': "\nint main() {\n    cout << solution() << endl;\n    return 0;\n}",
    # 'go': "\nfunc main() {    fmt.Println(solution())\n}\n",
    'java': "\n}",
    'js': "\nconsole.log(solution());\n",
    # 'php': "\n    echo solution();\n?>",
    'python': "\nprint(solution())",
    'r': "\ncat(solution())\n",
    # 'rust': "\n    println!(\"{}\", solution());\n}\n",
    # 'ts': "\nconsole.log(solution());\n"
}

FILE_EXTENSIONS = {
    'bash': '.sh',
    'c#': '.cs',
    'cpp': '.cpp',
    'go': '.go',
    'java': '.java',
    'js': '.js',
    'php': '.php',
    'python': '.py',
    'r': '.R',
    'rust': '.rs',
    'ts': '.ts'
}

EXECUTE_COMMANDS = {
    'bash': "bash {script_name}.sh",
    'c#': "dotnet run {script_name}.cs",
    'cpp': "g++ {script_name}.cpp -o {script_name}",
    'go': "go run {script_name}.go",
    'java': "java {script_name}.java",
    'js': "node {script_name}.js",
    'php': "php {script_name}.php",
    'python': "python {script_name}.py",
    'r': "Rscript {script_name}.R",
    'rust': "rustc {script_name}.rs -o {script_name}",
    'ts': "tsc {script_name}.ts"
}

output_statements = {
    'python': ['print('],
    'r': ['print(', 'cat('],
    'js': ['console.log('],
    'java': ['System.out.println(', 'System.out.print('],
    'cpp': ['cout']
}

import re


def delete_output(code, lang):
    # 构建输出语句的正则模式
    patterns = {
        'python': r'^\s*print\(.+\)',
        'r': r'^\s*(print|cat)\(.+\)',
        'js': r'^\s*console\.(log|info|warn|error)\(.+\)',
        'java': r'^\s*System\.out\.(println|print)\(.+\)',
        'cpp': r'^\s*cout\s*<<.+;'
    }
    
    pattern = patterns[lang]
    # 找到所有匹配的输出语句
    deleted_statements = re.findall(pattern, code, flags=re.MULTILINE)
    if len(deleted_statements) != 0:
        print(deleted_statements)
    # 使用正则替换
    cleaned_code = re.sub(pattern, '', code, flags=re.MULTILINE)
    # 移除可能产生的多余空行
    cleaned_code = re.sub(r'\n\s*\n', '\n', cleaned_code)
    return cleaned_code.strip()


def javaprocess(code):
    java_import = ""
    if "import" in code:
        imports = re.findall(r"import (.*);", code)
        for i in imports:
            java_import += f"import {i};\n"
        code = re.sub(r"import (.*);", "", code)
    
    class_main = re.search(r"public class \w+ {", code)
    if class_main:
        last_quote = code.rfind("}")
        code = code[class_main.end():last_quote]

    class_main = code.find("public static void main")
    if (class_main != -1):
        code = code[:class_main]
    
    return java_import, code


def cppprocess(code):
    # Remove include statements
    code = re.sub(r'#include <.*>', '', code)
    # Remove main function
    main_function = re.search(r'\w+ main\(\) {', code)
    if main_function:
        code = code[:main_function.start()]
    
    return code.replace("std::", "")