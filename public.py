import docker
import os, sys, json
from datetime import datetime

DockerClient = docker.from_env()

ConfigFile = 'config.json'

if len(sys.argv) >= 2:
    ConfigFile = sys.argv[1]

with open(ConfigFile, 'r') as fp:
    config: dict = json.load(fp)

def get_config(key: str, default=None):
    if default is None:
        return config[key]
    if not key in config.keys():
        return default
    return config[key]

CompilerSrc = config['compiler-src']      # path to the compiler source code (./src/)
CompilerBuild = config['compiler-build']  # path to compiler build artifact
CompilerFileName = 'compiler.jar'  # name of executable jar
CompilerPath = CompilerBuild + os.sep + CompilerFileName

TestcaseBaseDir = config['testcase-base']
TestcaseSelect = config['testcase-select']
NumParallel = config['num-parallel']

RebuildCompiler = config['rebuild-compiler']

RunType = config['run-type']

CacheSource = get_config('cache-source', False)
RpiAddresses = get_config('rpi-addresses', [])
LogDirBase = get_config('log-dir', 'logs')
LogDirHostBase = get_config('log-dir-host', 'logs')
TimeoutSecs = get_config('timeout', 60)

JvmOptions = get_config('jvm-options', "")

EnableOptimize = get_config('enable-optimize', False)
OptOption = "-O2" if EnableOptimize else ""

MemoryLimit = get_config('memory-limit', '256m')

logName = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + "_" + str(os.getpid())
logDir = os.path.realpath(os.path.join(LogDirBase, logName))
os.makedirs(logDir)

logDirHost = os.path.realpath(os.path.join(LogDirHostBase, logName))

results = [] # (series, name, verdict, comment, perf, stdin, stdout, answer)

def add_result(result):
    results.append(result)
