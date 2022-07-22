import requests
from urllib import parse
from concurrent.futures import ThreadPoolExecutor
import queue
import sys

API_UPLOAD_ELF = "/elf"
API_UPLOAD_ASM = "/asm"
API_INPUT = "/input"
API_OUTPUT = "/output"
API_PERF = "/perf"

def run_testcase_on_pi(rpi_address: str, case_name: str, target_file: str, input_file: str, output_file: str, perf_file: str, elf: bool):
    ApiUpload = API_UPLOAD_ELF if elf else API_UPLOAD_ASM
    # 发送 POST 请求传文件
    with open(target_file, "rb") as fp:
        resp = requests.post(url=parse.urljoin(rpi_address, ApiUpload), files={'file': fp})
        print('--- rpi {name} ---\nupload target returns {status}: {body}\n------'.format(name=case_name, status=resp.status_code, body=resp.text))
        if resp.status_code != 200:
            raise Exception("Failed upload target to pi (code={0}): {1}".format(resp.status_code, resp.text))
    # 发送 POST 请求传输入
    with open(input_file, "rb") as fp:
        resp = requests.post(url=parse.urljoin(rpi_address, API_INPUT), files={'file': fp})
        print('--- rpi {name} ---\ninput returns {status}: {body}\n------'.format(name=case_name, status=resp.status_code, body=resp.text))
        if resp.status_code != 200:
            raise Exception("Failed input to pi (code={0}): {1}".format(resp.status_code, resp.text))
    # 下载输出文件和性能文件
    with open(output_file, "w") as fp:
        resp = requests.get(url=parse.urljoin(rpi_address, API_OUTPUT))
        fp.write(resp.text)
        if resp.status_code != 200:
            raise Exception("Failed get output from pi (code={0})".format(resp.status_code))
    with open(perf_file, "w") as fp:
        resp = requests.get(url=parse.urljoin(rpi_address, API_PERF))
        fp.write(resp.text)
        if resp.status_code != 200:
            raise Exception("Failed get perf from pi (code={0})".format(resp.status_code))

Executor: ThreadPoolExecutor = None

rpi_idle_queue = queue.Queue()

def setup_rpi(addresses: list):
    real_addrs = []
    for addr in addresses:
        # test this addr
        try:
            requests.get(url=addr, timeout=2)
        except:
            print('Invalid rpi address: {0}'.format(addr), file=sys.stderr)
            continue    # pi-side service is offline.
        real_addrs.append(addr)
        rpi_idle_queue.put(addr)
    if len(real_addrs) == 0:
        print('No available rpi')
    Executor = ThreadPoolExecutor(max_workers=len(real_addrs))

# req: (case_name, target_file, input_file, output_file, perf_file, is_elf)
def submit_to_rpi_and_wait(req: tuple):
    def wrapper(req):
        rpi_addr = rpi_idle_queue.get()
        try:
            run_testcase_on_pi(rpi_addr, req[0], req[1], req[2], req[3], req[4], req[5])
            return None
        except Exception as e:
            # print(e)
            return e
        finally:
            rpi_idle_queue.put(rpi_addr)
    
    task = Executor.submit(wrapper, req)
    e = task.result()
    if e is not None:
        raise e
