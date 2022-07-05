import os
import html

from const import verdict_name, ACCEPTED

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

# 折叠过长的输入输出
def reduce_text(txt: str):
    limit = 100
    l = len(txt)
    if l > limit:
        return txt[:limit] + "<i>(... total {0} bytes)</i>".format(l)
    return txt

# 生成 HTML 评测结果
def display_result(results: dict, title: str):
    # (name, verdict, comment, perf, stdin, stdout, answer)
    table_rows = []
    for result in sorted(results, key=lambda r: r[0]):
        result_out = list(result)
        result_out[1] = verdict_name[result[1]]
        result_out = list(map(lambda s : html.escape(str(s)).replace('\n', '<br>'), result_out))
        # 评测结果颜色
        if result[1] == ACCEPTED:
            result_out[1] = "<font color=\"green\">" + result_out[1] + "</font>"
        else:
            result_out[1] = "<font color=\"red\">" + result_out[1] + "</font>"
        # 省略太长的输出
        result_out[4:7] = map(reduce_text, result_out[4:7])
        table_rows.append("".join(['<td>{0}</td>'.format(s) for s in result_out]))
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
