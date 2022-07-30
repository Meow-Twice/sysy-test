import requests
from urllib import parse
from concurrent.futures import ThreadPoolExecutor
import queue
from const import RUNTIME_ERROR

from logger import printLog
from util import add_result

API_UPLOAD_ELF  = "/elf"
API_UPLOAD_ASM  = "/asm"
API_INPUT       = "/input"
API_OUTPUT      = "/output"
API_PERF        = "/perf"

REQUEST_TIMEOUT = 65536

def run_testcase_on_pi(rpi_address: str, judge: dict):
    rpi_testcase_ident = 'rpi {name} @ {addr}'.format(name=judge['case_fullname'], addr=rpi_address)
    api_upload = API_UPLOAD_ELF if 'file_elf' in judge.keys() else API_UPLOAD_ASM
    file_upload = judge['file_elf'] if 'file_elf' in judge.keys() else judge['file_asm']
    # 发送 POST 请求传文件
    with open(file_upload, "rb") as fp:
        printLog('--- {0} uploading target ---'.format(rpi_testcase_ident))
        resp = requests.post(url=parse.urljoin(rpi_address, api_upload), data=fp, timeout=REQUEST_TIMEOUT)
        printLog('--- {0} upload target returns {1}:\n{2}\n------'.format(rpi_testcase_ident, resp.status_code, resp.text))
        if resp.status_code != 200:
            raise Exception("Failed upload target to {0} (code={1}): \n{2}".format(rpi_testcase_ident, resp.status_code, resp.text))
    # 发送 POST 请求传输入
    with open(judge['file_in'], "rb") as fp:
        printLog('--- {0} sending input ---'.format(rpi_testcase_ident))
        resp = requests.post(url=parse.urljoin(rpi_address, API_INPUT), data=fp, timeout=REQUEST_TIMEOUT)
        printLog('--- {0} input returns {1}:\n{2}\n------'.format(rpi_testcase_ident, resp.status_code, resp.text))
        if resp.status_code != 200:
            raise Exception("Failed input to {0} (code={1}): \n{2}".format(rpi_testcase_ident, resp.status_code, resp.text))
    # 下载输出文件和性能文件
    with open(judge['file_out'], "w") as fp:
        printLog('--- {0} retriving output ---'.format(rpi_testcase_ident))
        resp = requests.get(url=parse.urljoin(rpi_address, API_OUTPUT), timeout=REQUEST_TIMEOUT)
        printLog('--- {0} get output returns {1}: {2} bytes ---'.format(rpi_testcase_ident, resp.status_code, len(resp.text)))
        fp.write(resp.text)
        if resp.status_code != 200:
            raise Exception("Failed get output from {0} (code={1})".format(rpi_testcase_ident, resp.status_code))
    with open(judge['file_perf'], "w") as fp:
        printLog('--- {0} retriving perf ---'.format(rpi_testcase_ident))
        resp = requests.get(url=parse.urljoin(rpi_address, API_PERF), timeout=REQUEST_TIMEOUT)
        printLog('--- {0} get perf returns {1}: {2} bytes ---'.format(rpi_testcase_ident, resp.status_code, len(resp.text)))
        fp.write(resp.text)
        if resp.status_code != 200:
            raise Exception("Failed get perf from {0} (code={1})".format(rpi_testcase_ident, resp.status_code))

Executor: ThreadPoolExecutor = None

rpi_idle_queue = queue.Queue()

def setup_rpi(addresses: list):
    if len(addresses) == 0:
        return
    global Executor, rpi_idle_queue
    real_addrs = []
    for addr in addresses:
        # test this addr
        try:
            requests.get(url=addr, timeout=2)
        except:
            printLog('Invalid rpi address: {0}'.format(addr))
            continue    # pi-side service is offline.
        real_addrs.append(addr)
        rpi_idle_queue.put(addr)
    if len(real_addrs) == 0:
        printLog('No available rpi')
        return
    Executor = ThreadPoolExecutor(max_workers=len(real_addrs))

def submit_to_rpi(judge: dict, callback):
    def wrapper(judge: dict, callback):
        # printLog("wrapper {0}".format(judge))
        rpi_addr = rpi_idle_queue.get()
        try:
            run_testcase_on_pi(rpi_addr, judge)
            callback(judge)
        except Exception as e:
            comment = str(e)
            printLog('Runtime Error with Pi ({0}): {1}'.format(judge['case_fullname'], comment))
            add_result(judge['work_dir'], {
                'series_name': judge['series_name'], 'case_name': judge['case_name'], 'verdict': RUNTIME_ERROR,
                'comment': comment, 'perf': '', 'stdin': '', 'stdout': '', 'answer': ''
            })
        finally:
            rpi_idle_queue.put(rpi_addr)
    Executor.submit(wrapper, judge, callback)
    printLog('[Submit {0} to rpi waiting queue ...]'.format(judge['case_fullname']))

def wait_rpi_all():
    if Executor is not None:
        Executor.shutdown(wait=True)