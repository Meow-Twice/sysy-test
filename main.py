import os, json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from const import *
from public import *
from util import print_result, walk_testcase, display_result, archive_source
from tasks import build_compiler
from judge import test_one_case

if RebuildCompiler:
    build_compiler(DockerClient, CompilerSrc, CompilerBuild)

if CacheSource:
    archive_source(CompilerSrc, os.path.join(logDir, "src.tar.gz"))

testcases = walk_testcase(TestcaseBaseDir, TestcaseSelect)

# 使用线程池运行测试点
with ThreadPoolExecutor(max_workers=NumParallel) as pool:
    pool.map(test_one_case, testcases)

timeNow = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + "_" + str(os.getpid())

with open(os.path.join(logDir, 'result_' + timeNow + '.html'), 'w') as fp:
    fp.write(display_result(results, title=logName))

with open(os.path.join(logDir, 'result_' + timeNow + '.json'), 'w') as fp:
    json.dump(results, fp=fp)

print_result(results)