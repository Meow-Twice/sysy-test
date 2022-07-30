import os, stat, shutil

from const import *
from tasks import *
from util import answer_check, add_result
from public import *
from rpi import submit_to_rpi
from logger import printLog

judge_type = RunType

remove_elf_after_run = True

# testcase: {series_name, case_name, file_src, file_in, file_ans}
# judge_context: {series_name, case_name, work_dir, out_dir, work_dir_host, out_dir_host, 
#   file_src, file_src_host, file_in, file_in_host, file_ans, file_out, file_perf}
def test_one_case(testcase: dict):
    global judge_type
    judge = dict()
    series_name, case_name = judge['series_name'], judge['case_name'] = testcase['series_name'], testcase['case_name']
    judge['case_fullname'] = os.path.join(testcase['series_name'], testcase['case_name'])
    printLog('{0} start.'.format(judge['case_fullname']))
    # Resolve dir and filenames
    judge['work_dir'] = os.path.join(logDir, series_name, case_name)
    judge['out_dir'] = os.path.join(judge['work_dir'], 'output')
    # dirs on host (pass to docker -v)
    judge['work_dir_host'] = os.path.join(logDirHost, series_name, case_name)
    judge['out_dir_host'] = os.path.join(judge['work_dir_host'], 'output')
    os.makedirs(judge['work_dir'], mode=0o755, exist_ok=True)
    judge['file_src']       = os.path.join(judge['work_dir'], case_name + '.sy')
    judge['file_src_host']  = os.path.join(judge['work_dir_host'], case_name + '.sy')
    judge['file_in']        = os.path.join(judge['work_dir'], case_name + '.in')
    judge['file_in_host']   = os.path.join(judge['work_dir_host'], case_name + '.in')
    judge['file_ans']       = os.path.join(judge['work_dir'], case_name + '.out')
    judge['file_out']       = os.path.join(judge['work_dir'], 'output.txt')
    judge['file_perf']      = os.path.join(judge['work_dir'], 'perf.txt')

    # Prepare given files
    shutil.copy(testcase['file_src'], judge['file_src'])
    if not os.path.exists(testcase['file_in']):
        open(judge['file_in'], 'w').close() # create an empty file
    else:
        shutil.copy(testcase['file_in'], judge['file_in'])
    shutil.copy(testcase['file_ans'], judge['file_ans'])
    # Compile Testcase
    if judge_type == TYPE_INTERPRET:
        try:
            run_interpreter(DockerClient, judge['case_fullname'], CompilerPath, judge['file_src_host'], judge['file_in_host'], judge['out_dir_host'])
            shutil.copy(os.path.join(judge['out_dir'], 'output.txt'), judge['file_out'])
            shutil.copy(os.path.join(judge['out_dir'], 'perf.txt'), judge['file_perf'])
        except Exception as e:
            verdict = RUNTIME_ERROR
            comment = str(e)
            printLog('Interpret Error({0}): {1}'.format(judge['case_fullname'], comment))
            add_result(judge['work_dir'], {
                'series_name': series_name, 'case_name': case_name, 'verdict': verdict, 
                'comment': comment, 'perf': '', 'stdin': '', 'stdout': '', 'answer': ''
            })
            return
    else:
        try:
            if judge_type == TYPE_LLVM:
                compile_testcase(DockerClient, judge['case_fullname'], CompilerPath, judge['file_src_host'], judge['out_dir_host'], 'llvm')
            elif judge_type == TYPE_QEMU or judge_type == TYPE_RPI or judge_type == TYPE_RPI_ELF:
                compile_testcase(DockerClient, judge['case_fullname'], CompilerPath, judge['file_src_host'], judge['out_dir_host'], 'arm')
            else:
                printLog('Not Supported Judge Type: {0}'.format(judge_type))
                return
        except Exception as e:
            verdict = COMPILE_ERROR
            comment = str(e)
            printLog('Compile error ({0}): {1}'.format(judge['case_fullname'], comment))
            add_result(judge['work_dir'], {
                'series_name': series_name, 'case_name': case_name, 'verdict': verdict, 
                'comment': comment, 'perf': '', 'stdin': '', 'stdout': '', 'answer': ''
            })
            return
        # Get compiled target of testcase
        if judge_type == TYPE_LLVM:
            judge['file_ll'] = os.path.join(judge['work_dir'], case_name + '.ll') # LLVM
            judge['file_ll_host'] = os.path.join(judge['work_dir_host'], case_name + '.ll')
            shutil.copy(os.path.join(judge['out_dir'], 'test.ll'), judge['file_ll'])
        else:
            judge['file_asm'] = os.path.join(judge['work_dir'], case_name + '.S') # ARM
            judge['file_asm_host'] = os.path.join(judge['work_dir_host'], case_name + '.S')
            shutil.copy(os.path.join(judge['out_dir'], 'test.S'), judge['file_asm'])
        printLog('{0} compiled.'.format(judge['case_fullname']))
        # Run target code
        try:
            if judge_type == TYPE_LLVM:
                run_testcase(DockerClient, judge['case_fullname'], judge['file_ll_host'], judge['file_in_host'], judge['out_dir_host'], 'llvm')
                shutil.copy(os.path.join(judge['out_dir'], 'output.txt'), judge['file_out'])
                shutil.copy(os.path.join(judge['out_dir'], 'perf.txt'), judge['file_perf'])
            elif judge_type == TYPE_QEMU:
                judge['file_elf'] = os.path.join(judge['work_dir'], case_name + '.elf')
                judge['file_elf_host'] = os.path.join(judge['work_dir_host'], case_name + '.elf')
                open(judge['file_elf'], 'w').close()    # create an empty elf
                genelf_testcase(DockerClient, judge['case_fullname'], judge['file_asm_host'], judge['file_elf_host'], judge['out_dir_host'])
                os.chmod(judge['file_elf'], os.stat(judge['file_elf']).st_mode | stat.S_IEXEC)
                run_testcase(DockerClient, judge['case_fullname'], judge['file_elf_host'], judge['file_in_host'], judge['out_dir_host'], 'qemu')
                shutil.copy(os.path.join(judge['out_dir'], 'output.txt'), judge['file_out'])
                shutil.copy(os.path.join(judge['out_dir'], 'perf.txt'), judge['file_perf'])
            elif judge_type == TYPE_RPI:
                submit_to_rpi(judge, read_out_and_check)
                return  # get result is async
            elif judge_type == TYPE_RPI_ELF:
                judge['file_elf'] = os.path.join(judge['work_dir'], case_name + '.elf')
                judge['file_elf_host'] = os.path.join(judge['work_dir_host'], case_name + '.elf')
                open(judge['file_elf'], 'w').close()    # create an empty elf
                genelf_testcase(DockerClient, judge['case_fullname'], judge['file_asm_host'], judge['file_elf_host'], judge['out_dir_host'])
                submit_to_rpi(judge, read_out_and_check)
                return
            else:
                printLog('Not Supported Judge Type: {0}'.format(judge_type))
                return
        except Exception as e:
            verdict = RUNTIME_ERROR
            comment = str(e)
            printLog('Runtime error ({0}): {1}'.format(judge['case_fullname'], comment))
            add_result(judge['work_dir'], {
                'series_name': series_name, 'case_name': case_name, 'verdict': verdict, 
                'comment': comment, 'perf': '', 'stdin': '', 'stdout': '', 'answer': ''})
            return
        read_out_and_check(judge)

def read_out_and_check(judge: dict):
    if remove_elf_after_run:
        if 'file_elf' in judge.keys() and os.path.exists(judge['file_elf']):
            os.remove(judge['file_elf'])
    with open(judge['file_perf'], 'r') as fp:
        perf_text = fp.read()
    correct, comment = answer_check(judge['file_ans'], judge['file_out'])
    if not correct:
        with open(judge['file_in'], 'r') as fp:
            stdin_text = fp.read()
        with open(judge['file_out'], 'r') as fp:
            stdout_text = fp.read()
        with open(judge['file_ans'], 'r') as fp:
            answer_text = fp.read()
        add_result(judge['work_dir'], {
            'series_name': judge['series_name'], 'case_name': judge['case_name'], 'verdict': WRONG_ANSWER, 
            'comment': comment, 'perf': perf_text, 'stdin': stdin_text, 'stdout': stdout_text, 'answer': answer_text
        })
    else:
        add_result(judge['work_dir'], {
            'series_name': judge['series_name'], 'case_name': judge['case_name'], 'verdict': ACCEPTED, 
            'comment': comment, 'perf': perf_text, 'stdin': '', 'stdout': '', 'answer': ''
        })

