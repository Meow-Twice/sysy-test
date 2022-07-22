import docker
import os, sys, json
from datetime import datetime

DockerClient = docker.from_env()

ConfigFile = 'config.json'

if len(sys.argv) >= 2:
    ConfigFile = sys.argv[1]

with open(ConfigFile, 'r') as fp:
    config: dict = json.load(fp)

CompilerSrc = config['compiler-src']      # path to the compiler source code (./src/)
CompilerBuild = config['compiler-build']  # path to compiler build artifact
CompilerFileName = 'compiler.jar'  # name of executable jar
CompilerPath = CompilerBuild + os.sep + CompilerFileName

TestcaseBaseDir = config['testcase-base']
TestcaseSelect = config['testcase-select']
NumParallel = config['num-parallel']

RebuildCompiler = config['rebuild-compiler']

CacheSource = False
if 'cache-source' in config.keys():
    CacheSource = config['cache-source']

RunType = config['run-type']

RpiAddresses = []
if 'rpi-address' in config.keys():
    RpiAddresses = config['rpi-addresses']

LogDirBase = 'logs'
if 'log-dir' in config.keys():
    LogDirBase = config['log-dir']

LogDirHostBase = 'logs'
if 'log-dir-host' in config.keys():
    LogDirHostBase = config['log-dir-host']

TimeoutSecs = 60

if 'timeout' in config.keys():
    TimeoutSecs = config['timeout']

JvmOptions = ""
if 'jvm-options' in config.keys():
    JvmOptions = config['jvm-options']

logName = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + "_" + str(os.getpid())
logDir = os.path.realpath(os.path.join(LogDirBase, logName))
os.makedirs(logDir)

logDirHost = os.path.realpath(os.path.join(LogDirHostBase, logName))

results = [] # (series, name, verdict, comment, perf, stdin, stdout, answer)
