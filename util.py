import os
import json
import html
import tarfile
import prettytable

from const import verdict_name, ACCEPTED

# 遍历测试点
def walk_testcase(baseDir: str, dirs: list): # [(series_name, case_name, path_to_sy, path_to_in, path_to_out)]
    testcase_list = []
    for dir in dirs:
        _, _, files = os.walk(os.path.join(baseDir, dir)).__next__()
        for file in files:
            file: str
            if file.endswith('.sy'):
                name = file.split('.')[0]
                sy = os.path.realpath(os.path.join(baseDir, dir, file))
                file_in = os.path.realpath(os.path.join(baseDir, dir, name + '.in'))
                file_out = os.path.realpath(os.path.join(baseDir, dir, name + '.out'))
                testcase_list.append((dir, name, sy, file_in, file_out))
    return sorted(testcase_list, key=lambda x : (x[0], x[1]))

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

def get_summary(results: list) -> str:
    total_cases = len(results)
    passed_cases = len(list(filter(lambda x : x['verdict'] == ACCEPTED, results)))
    summary = 'Total {0} testcases, passed {1}.'.format(total_cases, passed_cases)
    return summary

# 生成 HTML 评测结果
def display_result(results: list, title: str):
    summary = get_summary(results)
    # (series, name, verdict, comment, perf, stdin, stdout, answer)
    table_rows = []
    for result in sorted(results, key=lambda r: (r['series_name'], r['case_name'])):
        result_out = [result[k] for k in ['series_name', 'case_name', 'verdict', 'comment', 'perf', 'stdin', 'stdout', 'answer']]
        result_out[2] = verdict_name[result['verdict']] # verdict
        result_out = list(map(lambda s : html.escape(str(s)).replace('\n', '<br>'), result_out))
        # 评测结果颜色
        if result['verdict'] == ACCEPTED:
            result_out[2] = "<font color=\"green\">" + result_out[2] + "</font>"
        else:
            result_out[2] = "<font color=\"red\">" + result_out[2] + "</font>"
        # 省略太长的输出
        result_out[4:] = map(reduce_text, result_out[4:])
        table_rows.append("".join(['<td>{0}</td>'.format(s) for s in result_out]))
    text = '''<html>
<head>
<title>{title}</title>
</head>
<body>
<p>{summary}</p>
<table border="1">
<tr> <th>series</th> <th>name</th> <th>verdict</th> <th>comment</th> <th>perf</th> <th>stdin</th> <th>stdout</th> <th>answer</th> </tr>
{body}
</table>
</body>
</html>'''.format(title=title, summary=summary, body="\n".join(['<tr>{0}</tr>'.format(s) for s in table_rows]))
    return text

def pretty_result(results: list):
    table = prettytable.PrettyTable(field_names=['series', 'case_name', 'verdict', 'comment', 'perf'])
    for r in sorted(results, key=lambda r: (r['series_name'], r['case_name'])):
        table.add_row((r['series_name'], r['case_name'], verdict_name[r['verdict']], r['comment'], reduce_text(r['perf'])))
    summary = get_summary(results)
    return "\n".join([str(table), summary])

def archive_source(src_dir: str, dst_file: str):
    with tarfile.open(dst_file, "w:gz") as tar:
        tar.add(src_dir, arcname=os.path.basename(src_dir))
