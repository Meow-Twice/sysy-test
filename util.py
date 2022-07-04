import os
import html

from const import verdict_name

# 遍历测试点
def walk_testcase(dir: str): # [(name, path_to_sy, path_to_in, path_to_out)]
    _, _, files = os.walk(dir).__next__()
    testcase_list = []
    for file in files:
        if file.endswith('.sy'):
            name = file.split('.')[0]
            sy = os.path.realpath(dir + os.sep + file)
            file_in = os.path.realpath(dir + os.sep + name + '.in')
            file_out = os.path.realpath(dir + os.sep + name + '.out')
            testcase_list.append((name, sy, file_in, file_out))
    return sorted(testcase_list, key=lambda x : x[0])

# 答案检查
def answer_check(ans_file: str, out_file: str): # (correct: bool, comment: str)
    with open(ans_file, 'r') as fp:
        ans_lines = fp.readlines()
    with open(out_file, 'r') as fp:
        out_lines = fp.readlines()
    if len(ans_lines) != len(out_lines):
        return False, 'We got {0} lines when we expected {1} lines.'.format(len(out_lines), len(ans_lines))
    l = len(ans_lines)
    for i in range(l):
        ans_line, out_line = ans_lines[i].strip(), out_lines[i].strip()
        if ans_line != out_line:
            return False, 'We got\n{0}\nWhen we expected\n{1}\nAt line {2}.'.format(out_line, ans_line, i + 1)
    return True, 'Correct!'

# 生成 HTML 评测结果
def display_result(results: dict, title: str):
    # (name, verdict, comment, perf, stdin, stdout, answer)
    table_rows = []
    for result in results:
        result_out = list(result)
        result_out[1] = verdict_name[result[1]]
        table_rows.append("".join(['<td>{0}</td>'.format(html.escape(str(s)).replace('\n', '<br>')) for s in result_out]))
    text = '''<html>
<head>
<title>{title}</title>
</head>
<body>
<table border="1">
<tr> <th>name</th> <th>verdict</th> <th>comment</th> <th>perf</th> <th>stdin</th> <th>stdout</th> <th>answer</th> </tr>
{body}
</table>
</body>
</html>'''.format(title=title, body="\n".join(['<tr>{0}</tr>'.format(s) for s in table_rows]))
    return text
