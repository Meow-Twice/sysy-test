import docker
import os

TIMEOUT_SECONDS = 10

def set_timeout(secs: int):
    global TIMEOUT_SECONDS
    TIMEOUT_SECONDS = secs

JAVA_IMAGE = 'openjdk:15-alpine'
BUILD_COMPILER_CMD = '/bin/sh -c "javac -d target -encoding \'utf-8\' $(find src -name \'*.java\' -type f); \
    cd target; echo \'**\' > .gitignore; mkdir -p META-INF; \
    echo -e \'Manifest-Version: 1.0\\r\\nMain-Class: Compiler\\r\\n\\r\\n\' > META-INF/MANIFEST.MF; \
    jar -cvfm compiler.jar META-INF/MANIFEST.MF *"'

COMPILE_LLVM_CMD = '/bin/sh -c "java -jar compiler.jar -emit-llvm -o test.ll test.sy; cp test.ll /output/"'
COMPILE_ARM_CMD = '/bin/sh -c "java -jar compiler.jar -S -o test.S test.sy; cp test.ll /output/"'

SYSY_IMAGE = "sysy:latest"
RUN_LLVM_CMD = '/bin/sh -c "sysy-run-llvm.sh test.ll <input.txt >output.txt 2>perf.txt; \
    echo $? >> exit.txt; cp perf.txt /output/; \
    if [ ! -z $(tail -c 1 output.txt) ]; then echo >> output.txt; fi; cat exit.txt >> output.txt; cp output.txt /output/"'
RUN_QEMU_CMD = '/bin/sh -c "sysy-elf.sh test.S; sysy-run-elf.sh test.elf <input.txt >output.txt 2>perf.txt; \
    echo $? >> exit.txt; cp perf.txt /output/; \
    if [ ! -z $(tail -c 1 output.txt) ]; then echo >> output.txt; fi; cat exit.txt >> output.txt; cp output.txt /output/"'

# 构建编译器, project_path 和 artifact_path 均为主机的路径 (使用 -v 选项挂载)
def build_compiler(client: docker.DockerClient, source_path: str, artifact_path: str) -> bool:
    container_name = 'compiler_{0}_build'.format(os.getpid())
    # cmd = '/bin/sh -ce "cd src; ls -la"'
    print('building compiler ......')
    container = client.containers.run(JAVA_IMAGE, command=BUILD_COMPILER_CMD, detach=True, name=container_name, working_dir='/project', volumes={
        os.path.realpath(source_path): {'bind': '/project/src', 'mode': 'ro'},
        os.path.realpath(artifact_path): {'bind': '/project/target', 'mode': 'rw'}
    }, auto_remove=True)
    try:
        container.wait(timeout=TIMEOUT_SECONDS)
    except Exception as e:
        container.kill()
        raise e
    print('compiler build finished.')

def compile_testcase(client: docker.DockerClient, compiler_path: str, sy_path: str, output_path: str, type: str='arm'):
    case_name = os.path.basename(sy_path).split('.')[0]
    container_name = 'compiler_{pid}_compile_{type}_{name}'.format(pid=os.getpid(), type=type, name=case_name)
    print('{0} - compiling'.format(case_name))
    if type == 'llvm':
        cmd = COMPILE_LLVM_CMD
    elif type == 'arm':
        cmd = COMPILE_ARM_CMD
    else:
        raise Exception("compile type {0} not support yet".format(type))
    container = client.containers.run(JAVA_IMAGE, command=cmd, detach=True, name=container_name, working_dir='/compiler', volumes={
        os.path.realpath(compiler_path): {'bind': '/compiler/compiler.jar', 'mode': 'ro'},
        os.path.realpath(sy_path): {'bind': '/compiler/test.sy', 'mode': 'ro'},
        os.path.realpath(output_path): {'bind': '/output/', 'mode': 'rw'}
    }, auto_remove=True)
    try:
        wait_body = container.wait(timeout=TIMEOUT_SECONDS)
        if wait_body['StatusCode'] != 0:
            raise Exception(wait_body)
    except Exception as e:
        try:
            container.kill()
        except:
            pass
        raise e
    print('{0} - compile finish.'.format(case_name))

def run_testcase(client: docker.DockerClient, code_path: str, input_path: str, output_path: str, type: str):
    case_name, extension_name = os.path.basename(code_path).split('.')
    container_name = 'compiler_{pid}_run_{type}_{name}'.format(pid=os.getpid(), type=type, name=case_name)
    print('{0} - running'.format(case_name))
    if type == 'llvm':
        cmd = RUN_LLVM_CMD
    elif type == 'qemu':
        cmd = RUN_QEMU_CMD
    else:
        raise Exception("run type {0} not support yet".format(type))
    container = client.containers.run(image=SYSY_IMAGE, command=cmd, detach=True, name=container_name, working_dir='/compiler', volumes={
        os.path.realpath(code_path): {'bind': '/compiler/test.' + extension_name, 'mode': 'ro'},
        os.path.realpath(input_path): {'bind': '/compiler/input.txt', 'mode': 'ro'},
        os.path.realpath(output_path): {'bind': '/output/', 'mode': 'rw'}
    }, auto_remove=True)
    try:
        container.wait(timeout=TIMEOUT_SECONDS)
    except Exception as e:
        try:
            container.kill()
        except:
            pass
        raise e
    print('{0} - run finish.'.format(case_name))
