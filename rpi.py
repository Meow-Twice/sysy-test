import requests
from urllib import parse
from concurrent.futures import ThreadPoolExecutor

pi_address = ""

def SetRpiAddress(addr: str):
    global pi_address
    pi_address = addr

API_UPLOAD_ELF = "/elf"
API_UPLOAD_ASM = "/asm"
API_INPUT = "/input"
API_OUTPUT = "/output"
API_PERF = "/perf"

def run_testcase_on_pi(case_name: str, target_file: str, input_file: str, output_file: str, perf_file: str, elf: bool):
    ApiUpload = API_UPLOAD_ELF if elf else API_UPLOAD_ASM
    # 发送 POST 请求传文件
    with open(target_file, "rb") as fp:
        resp = requests.post(url=parse.urljoin(pi_address, ApiUpload), files={'file': fp})
        print('--- rpi {name} ---\nupload target returns {status}: {body}\n------'.format(name=case_name, status=resp.status_code, body=resp.text))
        if resp.status_code != 200:
            raise Exception("Failed upload target to pi (code={0}): {1}".format(resp.status_code, resp.text))
    # 发送 POST 请求传输入
    with open(input_file, "rb") as fp:
        resp = requests.post(url=parse.urljoin(pi_address, API_INPUT), files={'file': fp})
        print('--- rpi {name} ---\ninput returns {status}: {body}\n------'.format(name=case_name, status=resp.status_code, body=resp.text))
        if resp.status_code != 200:
            raise Exception("Failed input to pi (code={0}): {1}".format(resp.status_code, resp.text))
    # 下载输出文件和性能文件
    with open(output_file, "w") as fp:
        resp = requests.get(url=parse.urljoin(pi_address, API_OUTPUT))
        fp.write(resp.text)
        if resp.status_code != 200:
            raise Exception("Failed get output from pi (code={0})".format(resp.status_code))
    with open(perf_file, "w") as fp:
        resp = requests.get(url=parse.urljoin(pi_address, API_PERF))
        fp.write(resp.text)
        if resp.status_code != 200:
            raise Exception("Failed get perf from pi (code={0})".format(resp.status_code))

Executor = ThreadPoolExecutor(max_workers=1)    # Only 1 thread can use pi

# req: (case_name, target_file, input_file, output_file, perf_file, is_elf)
def SubmitAndWait(req: tuple):
    def wrapper(req):
        try:
            run_testcase_on_pi(req[0], req[1], req[2], req[3], req[4], req[5])
        except Exception as e:
            # print(e)
            return e
        return None
    task = Executor.submit(wrapper, req)
    e = task.result()
    if e is not None:
        raise e
