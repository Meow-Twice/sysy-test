import docker
from const import *
from tasks import build_compiler, compile_testcase, run_testcase
from util import walk_testcase, answer_check, display_result
from datetime import datetime
import os, shutil
import json
from concurrent.futures import ThreadPoolExecutor

client = docker.from_env()

CONFIG_FILE = 'config.json'
with open(CONFIG_FILE, 'r') as fp:
    config = json.load(fp)

COMPILER_SRC_PATH = config['compiler-src']      # path to the compiler source code (./src/)
COMPILER_BUILD_PATH = config['compiler-build']  # path to compiler build artifact
COMPILER_NAME = 'compiler.jar'  # name of executable jar
CompilerPath = COMPILER_BUILD_PATH + os.sep + COMPILER_NAME

TESTCASE_PATH = config['testcase-path']
NUM_PARALLEL = config['num-parallel']

LOG_DIR_BASE = 'logs'

build_compiler(client, COMPILER_SRC_PATH, COMPILER_BUILD_PATH)

testcases = walk_testcase(TESTCASE_PATH)
testcases = testcases   # you can filter only part of the testcases here.

logName = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + "_" + str(os.getpid())
logDir = os.path.realpath(LOG_DIR_BASE + os.sep + logName)
os.makedirs(logDir)

results = [] # (name, verdict, comment, perf, stdin, stdout, answer)

def test_one_case(testcase): # testcase is a tuple of (name, path_to_sy, path_to_in, path_to_out)
    name, origin_sy, origin_in, origin_ans = testcase
    # 拷贝必需的文件
    workDir = logDir + os.sep + name
    outDir = workDir + os.sep + 'output'
    os.makedirs(workDir, mode=0o755, exist_ok=True)
    file_sy = workDir + os.sep + name + '.sy'
    file_in = workDir + os.sep + name + '.in'
    file_ans = workDir + os.sep + name + '.out'
    shutil.copy(origin_sy, file_sy)
    if not os.path.exists(origin_in):
        open(file_in, 'w').close() # create an empty file
    else:
        shutil.copy(origin_in, file_in)
    shutil.copy(origin_ans, file_ans)
    try:
        compile_testcase(client, CompilerPath, file_sy, outDir, 'llvm')
    except Exception as e:
        verdict = RUNTIME_ERROR
        comment = str(e)
        results.append((name, verdict, comment, '', '', '', ''))
        print('Testcase {0} COMPILE_ERROR with {1}'.format(name, comment))
        return
    file_code = workDir + os.sep + name + '.ll' # LLVM
    shutil.copy(outDir + os.sep + 'test.ll', file_code)
    try:
        run_testcase(client, file_code, file_in, outDir, 'llvm')
    except Exception as e:
        verdict = RUNTIME_ERROR
        comment = str(e)
        results.append((name, verdict, comment, '', '', '', ''))
        print('Testcase {0} RUNTIME_ERROR with {1}'.format(name, comment))
        return
    file_out = workDir + os.sep + 'output.txt'
    file_perf = workDir + os.sep + 'perf.txt'
    shutil.copy(outDir + os.sep + 'output.txt', file_out)
    shutil.copy(outDir + os.sep + 'perf.txt', file_perf)
    with open(file_perf, 'r') as fp:
        perf_text = fp.read()
    correct, comment = answer_check(file_ans, file_out)
    if not correct:
        with open(file_in, 'r') as fp:
            stdin_text = fp.read()
        with open(file_out, 'r') as fp:
            stdout_text = fp.read()
        with open(file_ans, 'r') as fp:
            answer_text = fp.read()
        results.append((name, WRONG_ANSWER, comment, perf_text, stdin_text, stdout_text, answer_text))
    else:
        results.append((name, ACCEPTED, comment, perf_text, '', '', ''))
    print('{0} finished: correct={1}'.format(name, correct))

# 使用线程池运行测试点
with ThreadPoolExecutor(max_workers=NUM_PARALLEL) as pool:
    pool.map(test_one_case, testcases)
    
with open(logDir + os.sep + 'results.html', 'w') as fp:
    fp.write(display_result(results, title=logName))
