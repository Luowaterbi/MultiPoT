ANNO = {
    "C++":"cpp",
    "Java":"java",
    "Python":"python",
    "Javascript":"javascript",
    "R":"r"
}

ANNO_U = {
    "cpp": "C++",
    "java": "Java",
    "python": "Python",
    "js": "Javascript",
    "r": "R"
}


CODE_PREFIX = {
    'C++': "#include <bits/stdc++.h>\n\nusing namespace std;\n\nauto solver() {\n",
    'Java': "public class Main {\n    public static void main(String[] args) {\n        System.out.println(solver());\n    }\npublic static double solver() {\n",
    'Javascript': "function solver() {\n",
    'Python': "def solver():\n",
    'R': "solver <- function() {\n",
}

CODE_SUFFIX = {
    'C++': "\nint main() {\n    cout << solver() << endl;\n    return 0;\n}",
    'Java': "\n}",
    'Javascript': "\nconsole.log(solver());\n",
    'Python': "\nprint(solver())",
    'R': "\ncat(solver())\n",
}