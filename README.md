# 编译测试脚本

用于编译比赛本地测试以及 CI 测试，支持五种模式:

- LLVM IR
- QEMU (ARM ELF, 由交叉编译器将汇编生成 ELF)
- RPi (ARM 汇编, 在 pi 上链接成 ELF)
- RPi (ARM ELF, 在 x86 主机上用交叉编译器将 ARM 汇编生成 ELF)
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

在当前目录创建 `config.json` (如采用其他文件名，需在调用本程序时以命令行参数形式给出)，格式如下:

```json
{
    "compiler-src": "path to your compiler source code",
    "compiler-build": "path to store build output of your compiler",
    "testcase-base": "path to the base of your testcase set",
    "testcase-select": ["functional", "performance"],
    "num-parallel": 8,
    "timeout": 60,
    "rebuild-compiler": true,
    "run-type": "llvm",
    "rpi-address": "http://192.168.1.2:8080"
}
```

其中:

- `compiler-src`: 编译器的源代码目录 (Java 工程目录下的 `src` 目录)
- `compiler-build`: 存放编译器的 `.class` 以及 `.jar` 的目录 (例如 Java 工程目录下的 `build` 目录)
- `testcase-base`: 测试用例集的根目录，该目录下可含有多个子目录，每个子目录代表一个测试集 (如功能测试集/性能测试集/自定义测试集, 子目录内只能是由 `.sy`, `.in` 和 `.out` 文件组成)
- `testcase-select`: 在 `testcase-base` 所指定的测试集根目录下选取一个或多个需要运行的测试集, 该参数为字符串数组类型
- `num-parallel`: 并发测试的线程数量，根据主机的 CPU 核心数量来选定，即平均每个核心测试一个用例。
- `timeout`: 超时时间，单位为秒，该参数可以缺省，缺省值为 60 秒。
- `rebuild-compiler`: 是否重新构建编译器, 如果不重新构建，须将已打包好的编译器置入 `compiler-build` 参数指定的目录下。(测试自己的编译器，此项选 `true` ；测试往届编译器，此项选 `false` )
- `run-type`: 测试的方式，字符串，可选值有:
  - `llvm`: 测试编译器前端，目标代码为 LLVM IR
  - `qemu`: 目标代码为 arm 汇编，使用交叉编译器生成 ELF 并用 qemu 在 x86 机器上测试目标程序
  - `rpi`: 目标代码为 arm 汇编，通过 API 在树莓派上链接生成 ELF 并运行
  - `rpi-elf`: 目标代码为 arm 汇编，用交叉编译器生成 ELF 并通过 API 在树莓派上执行
  - `interpret`: 编译器直接解释执行待编译的程序，读取标准输入并给出标准输出
- `rpi-address`: 树莓派的地址 (API HTTP 地址)，如果不运行树莓派的测试，该参数可以缺省

以上三个路径均为**绝对路径**。

### 必需的 docker 镜像

- Java JDK 镜像: `docker pull openjdk:15-alpine`
- SysY 测试镜像: 基于 GitHub 仓库构建, `git clone git@github.com:dhy2000/sysy-docker.git; cd sysy-docker; ./docker-build.sh` 。镜像名称为 `sysy:latest` 。

## 运行方法

完成上述所有准备工作后，在激活虚拟环境后执行 `python3 -u main.py` 即可开始测试。测试结果位于 `logs` 目录中。

如果使用的配置文件不是 `config.json` ，则需将配置文件作为第一个命令行参数传入，示例: `python3 -u main.py config-custom.json` 。

## 评测结果

结果默认保存在当前目录的 `logs` 文件夹，每次运行脚本生成一份评测记录，每份记录一个文件夹，名称格式为 "启动时间+进程号"。一份评测记录内包含：

- html 和 json 格式的评测结果摘要
- 如果 `rebuild-compiler` 参数为 `true` ，则保存一份压缩的编译器源代码
- 按测试集和测试用例划分的，每个用例一个目录，含有测试用例的源程序、标准输入、期望输出、编译结果、运行输出等
