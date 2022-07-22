# 编译测试脚本

用于 SysY 编译器的本地测试以及 CI 测试，支持五种模式:

- LLVM IR
- QEMU (ARM ELF, 由交叉编译器将汇编生成 ELF)
- 树莓派 (传输 ARM 汇编, 在 pi 上链接成 ELF)
- 树莓派 (传输 ARM ELF, 在 x86 主机上用交叉编译器对汇编代码进行链接)
- 解释器模式 (解释执行中间代码)

## 环境建立说明

（以下命令需要在该工程所在目录下执行）

### Python 虚拟环境

```shell
python3 -m virtualenv .venv     # 建立 Python 虚拟环境 (需要使用 virtualenv 模块)
source .venv/bin/activate       # 激活虚拟环境
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple # 安装依赖模块
```

### 配置文件

在当前目录创建 `config.json` (如采用其他文件名，需在调用本程序时以命令行参数形式给出)，格式如下 (实际的配置文件不要包含 JSON 注释):

```jsonc
{
    "compiler-src": "path to your compiler source code",              // 编译器的源代码目录 (Java 工程目录下的 `src` 目录)
    "compiler-build": "path to store build output of your compiler",  // 存放编译器的 `.class` 以及 `.jar` 的目录 (例如 Java 工程目录下的 `build` 目录)
    "testcase-base": "path to the base of your testcase set",         // 测试用例集的根目录，该目录下可含有多个子目录，每个子目录代表一个测试集
    "testcase-select": ["functional", "performance"],                 // 在 `testcase-base` 所指定的测试集根目录下选取一个或多个需要运行的测试集, 该参数为字符串数组类型
    "num-parallel": 8,                                                // 并发测试的线程数量，根据主机的 CPU 核心数量来选定，即平均每个核心测试一个用例。
    "timeout": 60,                                                    // 超时时间，单位为秒，该参数可以缺省，缺省值为 60 秒。
    "rebuild-compiler": true,                                         // 是否重新构建编译器
    "cache-source": true,                                             // 是否将编译器源代码打包保存到评测记录中，可以缺省，默认值 false
    "jvm-options": "",                                                // JVM 参数，例如 "-ea"，缺省值为空
    "run-type": "llvm",                                               // 可选值 "llvm", "qemu", "rpi", "rpi-elf", "interpret"
    "rpi-addresses": ["http://192.168.1.2:9000"],                     // 树莓派 API 地址列表 (如不测试树莓派可留空)
    "log-dir": "logs",                                                // 评测记录存放路径 (可以是相对路径) 缺省值为 `logs`
    "log-dir-host": "logs",                                           // 评测记录在主机上的路径 (使用 docker 运行评测脚本时才需要, 直接在主机上运行可缺省)
}
```

其中:

- 一个测试集 (位于 `testcase-base` 目录下的一个子目录, 通过 `testcase-select` 参数选定)为一个目录，内部由 `.sy`, `.in` 和 `.out` 文件组成。
- 测试自己的编译器，`rebuild-compiler` 参数应为 `true` ；测试往届编译器，此参数为 `false`，此时应将打包好的往届编译器命名为 `compiler.jar` 并置入 `compiler-build` 目录下。
- `run-type` 参数的取值和含义对应：
  - `llvm`: 测试编译器前端，目标代码为 LLVM IR
  - `qemu`: 目标代码为 arm 汇编，使用交叉编译器生成 ELF 并用 qemu 在 x86 机器上测试目标程序
  - `rpi`: 目标代码为 arm 汇编，通过 API 在树莓派上链接生成 ELF 并运行
  - `rpi-elf`: 目标代码为 arm 汇编，用交叉编译器生成 ELF 并通过 API 在树莓派上执行
  - `interpret`: 编译器直接解释执行待编译的程序，读取标准输入并给出标准输出
- `compiler-src`, `compiler-build`, `testcase-base` 三个路径须使用绝对路径。

### 必需的 docker 镜像

- Java JDK 镜像: `docker pull openjdk:15-alpine`
- SysY 测试镜像: 基于 GitHub 仓库构建, `git clone git@github.com:dhy2000/sysy-docker.git; cd sysy-docker; ./docker-build.sh` 。镜像名称为 `sysy:latest` 。

## 运行方法

### 在主机上运行

完成上述所有准备工作后，在激活虚拟环境后执行 `python3 -u main.py` 即可开始测试。测试结果位于 `logs` 目录中。

如果使用的配置文件不是 `config.json` ，则需将配置文件作为第一个命令行参数传入，示例: `python3 -u main.py config-custom.json` 。

### 在 Docker 容器中运行

根据 `Dockerfile` 构建 docker 镜像。由镜像生成容器时:

- 使用 `-v` 选项将主机上的 `/var/run/docker.sock` 挂载到容器内的相同路径，实现 docker in docker
- 测试用例存放目录和评测结果保存目录，需通过 `-v` 选项挂载到容器
- 配置文件也需挂载到容器

评测脚本启动 java 与 SysY 的 docker 容器用来执行编译器或工具链，需使用 `-v` 选项挂载文件。当评测脚本运行在 docker 容器中时，由于 docker in docker 的 `-v` 只能挂载主机上的目录 (而不是评测脚本所在容器的目录)，因此在编写配置文件时需要注意:

- `compiler-src` 和 `compiler-build` 使用宿主机路径 (绝对路径) 且无需挂载到评测脚本容器中, `cache-source` 为 `false` 或不填
- `testcase-base` 使用评测脚本所在容器内的路径 (绝对路径)
- `log-dir` 使用评测脚本容器内的路径 (可以用相对路径也可以用绝对路径)
- `log-dir-host` 参数，值为主机上与 `log-dir` 挂载绑定的路径 (绝对路径)

构建 docker 镜像:

```shell
docker build -t "sysy-test:latest" .
```

启动并进入容器:

```shell
docker run -it --rm --name=sysy-test \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ${TESTCASE_BASE}:/testcase/ \
    -v ${LOG_HOST_DIR}:/logs/ \
    -v $(realpath config.json):/app/config.json \
    sysy-test:latest /bin/bash
```

（其中 `${TESTCASE_BASE}` 和 `${LOG_HOST_DIR}` 替换成实际的测试集和测试结果目录，配置文件中 `testcase-base` 为 `/testcase/`, `log-dir` 为 `/logs/` ） 

## 评测结果

结果默认保存在当前目录的 `logs` 文件夹，每次运行脚本生成一份评测记录，每份记录一个文件夹，名称格式为 "启动时间+进程号"。一份评测记录内包含：

- html 和 json 格式的评测结果摘要
- 如果 `cache-source` 参数为 `true` ，则保存一份压缩的编译器源代码
- 按测试集和测试用例划分的，每个用例一个目录，含有测试用例的源程序、标准输入、期望输出、编译结果、运行输出等
