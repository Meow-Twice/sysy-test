import docker
import os, sys, json
from datetime import datetime

DockerClient = docker.from_env()

ConfigFile = 'config.json'

if len(sys.argv) >= 2:
    ConfigFile = sys.argv[1]

with open(ConfigFile, 'r') as fp:
    config = json.load(fp)

CompilerSrc = config['compiler-src']      # path to the compiler source code (./src/)
CompilerBuild = config['compiler-build']  # path to compiler build artifact
CompilerFileName = 'compiler.jar'  # name of executable jar
CompilerPath = CompilerBuild + os.sep + CompilerFileName

TestcaseBaseDir = config['testcase-base']
TestcaseSelect = config['testcase-select']
NumParallel = config['num-parallel']

RebuildCompiler = config['rebuild-compiler']
RunType = config['run-type']

RpiAddress = ""
if 'rpi-address' in config.keys():
    RpiAddress = config['rpi-address']

LogDirBase = 'logs'

TimeoutSecs = 60

if 'timeout' in config.keys():
    TimeoutSecs = config['timeout']

logName = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + "_" + str(os.getpid())
logDir = os.path.realpath(LogDirBase + os.sep + logName)
os.makedirs(logDir)

results = [] # (series, name, verdict, comment, perf, stdin, stdout, answer)
