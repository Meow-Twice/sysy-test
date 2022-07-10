import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from const import *
from util import walk_testcase, display_result
from public import *
from tasks import build_compiler
from judge import *

if RebuildCompiler:
    build_compiler(DockerClient, CompilerSrc, CompilerBuild)

testcases = walk_testcase(TestcaseBaseDir, TestcaseSelect)
SetJudgeType(RunType)

# 使用线程池运行测试点
with ThreadPoolExecutor(max_workers=NumParallel) as pool:
    pool.map(test_one_case, testcases)

timeNow = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + "_" + str(os.getpid())

with open(logDir + os.sep + 'result_' + timeNow + '.html', 'w') as fp:
    fp.write(display_result(results, title=logName))
