import docker
from docker.models.containers import Container
import os

from public import *

def wrap_cmd(cmd: str) -> str:
    return '/bin/sh -c "{0}"'.format(cmd.replace("\"", "\\\""))

def container_wait(container: Container):
    try:
        container.wait(timeout=TimeoutSecs)
    except Exception as e:
        try:
            container.kill()
        except:
            pass
        raise e

JavaImage = 'openjdk:15-alpine'

CmdBuildCompiler = 'javac -d target -encoding \'utf-8\' $(find src -name \'*.java\' -type f); \
    cd target; echo \'**\' > .gitignore; mkdir -p META-INF; \
    echo -e \'Manifest-Version: 1.0\\r\\nMain-Class: Compiler\\r\\n\\r\\n\' > META-INF/MANIFEST.MF; \
    jar -cvfm compiler.jar META-INF/MANIFEST.MF *'

CmdCompileLLVM  = 'java -jar compiler.jar -emit-llvm -o test.ll test.sy; cp test.ll /output/'
CmdCompileARM   = 'java -jar compiler.jar -S -o test.S test.sy; cp test.S /output/'

CmdCompileAndRunPcode = 'java -jar compiler.jar -pcode test.S < input.txt >output.txt 2>perf.txt; cp perf.txt /output/; cp output.txt /output/'

SysyImage = "sysy:latest"
CmdGenElf = 'sysy-elf.sh test.S 2>err.txt; cp err.txt /output/; cp test.elf /output/'

CmdRunLLVM = 'sysy-run-llvm.sh test.ll <input.txt >output.txt 2>perf.txt; \
    echo $? >> exit.txt; cp perf.txt /output/; \
    if [ ! -z $(tail -c 1 output.txt) ]; then echo >> output.txt; fi; cat exit.txt >> output.txt; cp output.txt /output/'

CmdRunQemu = 'sysy-run-elf.sh test.elf <input.txt >output.txt 2>perf.txt; \
    echo $? >> exit.txt; cp perf.txt /output/; \
    if [ ! -z $(tail -c 1 output.txt) ]; then echo >> output.txt; fi; cat exit.txt >> output.txt; cp output.txt /output/'

# 构建编译器, project_path 和 artifact_path 均为主机的路径 (使用 -v 选项挂载)
def build_compiler(client: docker.DockerClient, source_path: str, artifact_path: str) -> bool:
    container_name = 'compiler_{0}_build'.format(os.getpid())
    # cmd = '/bin/sh -ce "cd src; ls -la"'
    print('building compiler ......')
    container: Container = client.containers.run(JavaImage, command=wrap_cmd(CmdBuildCompiler), detach=True, name=container_name, working_dir='/project', volumes={
        os.path.realpath(source_path): {'bind': '/project/src', 'mode': 'ro'},
        os.path.realpath(artifact_path): {'bind': '/project/target', 'mode': 'rw'}
    }, auto_remove=True)
    container_wait(container)
    print('compiler build finished.')

def compile_testcase(client: docker.DockerClient, series_name: str, case_name: str, compiler_path: str, sy_path: str, output_path: str, type: str='arm'):
    fullname = os.path.join(series_name, case_name)
    container_name = 'compiler_{pid}_compile_{type}_{series}_{name}'.format(pid=os.getpid(), type=type, series=series_name, name=case_name)
    print('{0} - compiling'.format(fullname))
    if type == 'llvm':
        cmd = CmdCompileLLVM
    elif type == 'arm':
        cmd = CmdCompileARM
    else:
        raise Exception("compile type {0} not support yet".format(type))
    container: Container = client.containers.run(JavaImage, command=wrap_cmd(cmd), detach=True, name=container_name, working_dir='/compiler', volumes={
        os.path.realpath(compiler_path): {'bind': '/compiler/compiler.jar', 'mode': 'ro'},
        os.path.realpath(sy_path): {'bind': '/compiler/test.sy', 'mode': 'ro'},
        os.path.realpath(output_path): {'bind': '/output/', 'mode': 'rw'}
    }, auto_remove=True)
    container_wait(container)
    print('{0} - compile finish.'.format(fullname))

def genelf_testcase(client: docker.DockerClient, series_name: str, case_name: str, code_path: str, output_path: str):
    fullname = os.path.join(series_name, case_name)
    container_name = 'compiler_{pid}_genelf_{series}_{name}'.format(pid=os.getpid(), series=series_name, name=case_name)
    print(code_path)
    assert code_path.endswith('.S')
    print('{0} - elf generate begin'.format(fullname))
    container: Container = client.containers.run(image=SysyImage, command=wrap_cmd(CmdGenElf), detach=True, name=container_name, working_dir='/compiler', volumes={
        os.path.realpath(code_path): {'bind': '/compiler/test.S', 'mode': 'ro'},
        os.path.realpath(output_path): {'bind': '/output/', 'mode': 'rw'}
    }, auto_remove=True)
    container_wait(container)
    print('{0} - elf generated.'.format(fullname))

def run_testcase(client: docker.DockerClient, series_name: str, case_name: str, code_path: str, input_path: str, output_path: str, type: str):
    fullname = os.path.join(series_name, case_name)
    _, extension_name = os.path.basename(code_path).split('.')
    container_name = 'compiler_{pid}_run_{type}_{series}_{name}'.format(pid=os.getpid(), type=type, series=series_name, name=case_name)
    print('{0} - running'.format(fullname))
    if type == 'llvm':
        cmd = CmdRunLLVM
    elif type == 'qemu':
        cmd = CmdRunQemu
    else:
        raise Exception("run type {0} not support yet".format(type))
    container: Container = client.containers.run(image=SysyImage, command=wrap_cmd(cmd), detach=True, name=container_name, working_dir='/compiler', volumes={
        os.path.realpath(code_path): {'bind': '/compiler/test.' + extension_name, 'mode': 'ro'},
        os.path.realpath(input_path): {'bind': '/compiler/input.txt', 'mode': 'ro'},
        os.path.realpath(output_path): {'bind': '/output/', 'mode': 'rw'}
    }, auto_remove=True)
    container_wait(container)
    print('{0} - run finish.'.format(fullname))

def run_pcode(client: docker.DockerClient, series_name: str, case_name: str, compiler_path: str, sy_path: str, input_path: str, output_path: str):
    _, extension_name = os.path.basename(sy_path).split('.')
    assert extension_name == '.sy'
    container_name = 'compiler_{pid}_pcode_{series}_{name}'.format(pid=os.getpid(), series_name=series_name, name=case_name)
    print('{0} - pcode begin.'.format(case_name))
    container: Container = client.containers.run(image=JavaImage, command=wrap_cmd(CmdCompileAndRunPcode), detach=True, name=container_name, working_dir='/compiler', volumes={
        os.path.realpath(compiler_path): {'bind': '/compiler/compiler.jar', 'mode': 'ro'},
        os.path.realpath(sy_path): {'bind': '/compiler/test.sy', 'mode': 'ro'},
        os.path.realpath(input_path): {'bind': '/compiler/input.txt', 'mode': 'ro'},
        os.path.realpath(output_path): {'bind': '/output/', 'mode': 'rw'}
    }, auto_remove=True)
    container_wait(container)
    print('{0} - pcode done.'.format(case_name))
