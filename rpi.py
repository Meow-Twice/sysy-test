import requests
from urllib import parse
from concurrent.futures import ThreadPoolExecutor
import queue

from logger import printLog

API_UPLOAD_ELF = "/elf"
API_UPLOAD_ASM = "/asm"
API_INPUT = "/input"
API_OUTPUT = "/output"
API_PERF = "/perf"

REQUEST_TIMEOUT = 65536

def run_testcase_on_pi(rpi_address: str, case_name: str, target_file: str, input_file: str, output_file: str, perf_file: str, elf: bool):
    rpi_testcase_ident = 'rpi {name} @ {addr}'.format(name=case_name, addr=rpi_address)
    ApiUpload = API_UPLOAD_ELF if elf else API_UPLOAD_ASM
    # 发送 POST 请求传文件
    with open(target_file, "rb") as fp:
        printLog('--- {0} uploading target ---'.format(rpi_testcase_ident))
        resp = requests.post(url=parse.urljoin(rpi_address, ApiUpload), data=fp, timeout=REQUEST_TIMEOUT)
        printLog('--- {0} upload target returns {1}:\n{2}\n------'.format(rpi_testcase_ident, resp.status_code, resp.text))
        if resp.status_code != 200:
            raise Exception("Failed upload target to {0} (code={1}): \n{2}".format(rpi_testcase_ident, resp.status_code, resp.text))
    # 发送 POST 请求传输入
    with open(input_file, "rb") as fp:
        printLog('--- {0} sending input ---'.format(rpi_testcase_ident))
        resp = requests.post(url=parse.urljoin(rpi_address, API_INPUT), data=fp, timeout=REQUEST_TIMEOUT)
        printLog('--- {0} input returns {1}:\n{2}\n------'.format(rpi_testcase_ident, resp.status_code, resp.text))
        if resp.status_code != 200:
            raise Exception("Failed input to {0} (code={1}): \n{2}".format(rpi_testcase_ident, resp.status_code, resp.text))
    # 下载输出文件和性能文件
    with open(output_file, "w") as fp:
        printLog('--- {0} retriving output ---'.format(rpi_testcase_ident))
        resp = requests.get(url=parse.urljoin(rpi_address, API_OUTPUT), timeout=REQUEST_TIMEOUT)
        printLog('--- {0} get output returns {1}: {2} bytes ---'.format(rpi_testcase_ident, resp.status_code, len(resp.text)))
        fp.write(resp.text)
        if resp.status_code != 200:
            raise Exception("Failed get output from {0} (code={1})".format(rpi_testcase_ident, resp.status_code))
    with open(perf_file, "w") as fp:
        printLog('--- {0} retriving perf ---'.format(rpi_testcase_ident))
        resp = requests.get(url=parse.urljoin(rpi_address, API_PERF), timeout=REQUEST_TIMEOUT)
        printLog('--- {0} get perf returns {1}: {2} bytes ---'.format(rpi_testcase_ident, resp.status_code, len(resp.text)))
        fp.write(resp.text)
        if resp.status_code != 200:
            raise Exception("Failed get perf from {0} (code={1})".format(rpi_testcase_ident, resp.status_code))

Executor: ThreadPoolExecutor = None

rpi_idle_queue = queue.Queue()

def setup_rpi(addresses: list):
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

# req: (case_name, target_file, input_file, output_file, perf_file, is_elf)
def submit_to_rpi_and_wait(req: tuple):
    def wrapper(req):
        rpi_addr = rpi_idle_queue.get()
        try:
            run_testcase_on_pi(rpi_addr, req[0], req[1], req[2], req[3], req[4], req[5])
            return None
        except Exception as e:
            return e
        finally:
            rpi_idle_queue.put(rpi_addr)
    task = Executor.submit(wrapper, req)
    printLog('[Submit {0} to rpi waiting queue ...]'.format(req[0]))
    e = task.result()
    if e is not None:
        raise e
