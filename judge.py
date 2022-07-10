import os, shutil
from tasks import compile_testcase, genelf_testcase, run_testcase
from util import answer_check
from public import logDir, DockerClient, CompilerPath, results
from const import *
from rpi import SubmitAndWait

JudgeType = ''

def SetJudgeType(type: str):
    global JudgeType
    JudgeType = type

# testcase is a tuple of (series_name, case_name, path_to_sy, path_to_in, path_to_out)
def test_one_case(testcase: tuple): 
    global JudgeType
    series_name, case_name, origin_sy, origin_in, origin_ans = testcase
    full_name = os.path.join(series_name, case_name)
    print('{0} start.'.format(full_name))

    # Resolve dir and filenames
    workDir = os.path.join(logDir, series_name, case_name)
    outDir = os.path.join(workDir, 'output')
    os.makedirs(workDir, mode=0o755, exist_ok=True)
    file_sy = os.path.join(workDir, case_name + '.sy')
    file_in = os.path.join(workDir, case_name + '.in')
    file_ans = os.path.join(workDir, case_name + '.out')
    file_out = os.path.join(workDir, 'output.txt')
    file_perf = os.path.join(workDir, 'perf.txt')

    # Prepare given files
    shutil.copy(origin_sy, file_sy)
    if not os.path.exists(origin_in):
        open(file_in, 'w').close() # create an empty file
    else:
        shutil.copy(origin_in, file_in)
    shutil.copy(origin_ans, file_ans)
    # Compile Testcase
    if JudgeType == TYPE_PCODE:
        print('pcode test is not supported yet.')
        return
    try:
        if JudgeType == TYPE_LLVM:
            compile_testcase(DockerClient, series_name, case_name, CompilerPath, file_sy, outDir, 'llvm')
        elif JudgeType == TYPE_QEMU or JudgeType == TYPE_RPI or JudgeType == TYPE_RPI_ELF:
            compile_testcase(DockerClient, series_name, case_name, CompilerPath, file_sy, outDir, 'arm')
        else:
            print('Not Supported Judge Type: {0}'.format(JudgeType))
            return
    except Exception as e:
        verdict = RUNTIME_ERROR
        comment = str(e)
        results.append((series_name, case_name, verdict, comment, '', '', '', ''))
        print('Testcase {0} COMPILE_ERROR with {1}'.format(full_name, comment))
        return
    # Get compiled target of testcase
    if JudgeType == TYPE_LLVM:
        file_code = os.path.join(workDir, case_name + '.ll') # LLVM
        shutil.copy(os.path.join(outDir, 'test.ll'), file_code)
    else:
        file_code = os.path.join(workDir, case_name + '.S') # ARM
        shutil.copy(os.path.join(outDir, 'test.S'), file_code)
    
    # Run target code
    try:
        if JudgeType == TYPE_LLVM:
            run_testcase(DockerClient, series_name, case_name, file_code, file_in, outDir, 'llvm')
            shutil.copy(os.path.join(outDir, 'output.txt'), file_out)
            shutil.copy(os.path.join(outDir, 'perf.txt'), file_perf)
        elif JudgeType == TYPE_QEMU:
            genelf_testcase(DockerClient, series_name, case_name, file_code, outDir)
            file_elf = os.path.join(workDir, case_name + '.elf')
            shutil.copy(os.path.join(outDir, 'test.elf'), file_elf)
            run_testcase(DockerClient, series_name, case_name, file_elf, file_in, outDir, 'qemu')
            shutil.copy(os.path.join(outDir, 'output.txt'), file_out)
            shutil.copy(os.path.join(outDir, 'perf.txt'), file_perf)
        elif JudgeType == TYPE_RPI:
            SubmitAndWait((full_name, file_code, file_in, file_out, file_perf, False))
        elif JudgeType == TYPE_RPI_ELF:
            genelf_testcase(DockerClient, series_name, case_name, file_sy, outDir)
            file_elf = os.path.join(workDir, case_name + '.elf')
            shutil.copy(os.path.join(outDir, 'test.elf'), file_elf)
            SubmitAndWait((full_name, file_elf, file_in, file_out, file_perf, True))
        else:
            print('Not Supported Judge Type: {0}'.format(JudgeType))
            return
    except Exception as e:
        verdict = RUNTIME_ERROR
        comment = str(e)
        results.append((series_name, case_name, verdict, comment, '', '', '', ''))
        print('Testcase {0} RUNTIME_ERROR with {1}'.format(full_name, comment))
        return
    
    # Read result and check
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
        results.append((series_name, case_name, WRONG_ANSWER, comment, perf_text, stdin_text, stdout_text, answer_text))
    else:
        results.append((series_name, case_name, ACCEPTED, comment, perf_text, '', '', ''))
    print('{0} finished: correct={1}'.format(full_name, correct))