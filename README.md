# 编译比赛评测机 (自用)

用于 SysY 编译器的本地测试以及 CI 测试，支持多种模式:

- LLVM IR (仅测试编译器前端)
- QEMU (ARM ELF, 由交叉编译器将汇编生成 ELF)
- 树莓派 (传输 ARM 汇编, 在 pi 上链接成 ELF)
- 树莓派 (传输 ARM ELF, 在 x86 主机上用交叉编译器对汇编代码进行链接)

本队伍编译器基本情况：用 Java 语言开发编译器，使用 LLVM IR 作为中层表示，前端 Lexer 和 Parser 自行编写，未使用 Antlr 等自动分析工具。（暂不支持 Antlr 和 C/C++ 开发的编译器）

## 环境建立说明

（以下命令需要在该工程所在目录下执行）

### Python 虚拟环境

```shell
python3 -m virtualenv .venv     # 建立 Python 虚拟环境 (需要使用 virtualenv 模块)
source .venv/bin/activate       # 激活虚拟环境
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple # 安装依赖模块
```

### Docker 与必需的镜像

本评测机使用 docker 来运行自己的编译器以及 gcc/llvm 工具链。[安装说明](https://docs.docker.com/engine/install/)

需要准备的镜像：

- Java OpenJDK 15: 镜像名称 `openjdk:15-alpine`
  - 在终端执行 `docker pull openjdk:15-alpine` 以获取。
- GCC 与 LLVM 工具链: 镜像名称 `sysy:latest` 
  - 克隆 [sysy-docker](https://github.com/Meow-Twice/sysy-docker) 仓库，并执行 `docker-build.sh` 构建镜像。

### 测试用例准备

参考 [测试用例存储说明](./testcases.md) 。

### 对接编译器

为了使用此评测机，编译器需要支持的命令行参数：

- 输出 LLVM IR: `java -jar compiler.jar -emit-llvm -o test.ll test.sy [-O2]`
- 输出汇编代码: `java -jar compiler.jar -S -o test.S test.sy [-O2]`
- 同时输出 LLVM 和汇编: `java -jar compiler.jar -emit-llvm -o test.ll -S -o test.S test.sy [-O2]`

### 配置文件

评测配置文件为 JSON 格式，参数如下 (实际的配置文件**不要包含注释**):

```jsonc
{
    "compiler-src": "path to your compiler source code",              // 编译器的源代码目录 (Java 工程目录下的 `src` 目录)
    "compiler-build": "path to store build output of your compiler",  // 存放编译器的 `.class` 以及 `.jar` 的目录 (例如 Java 工程目录下的 `build` 目录)
    "testcase-base": "path to the base of your testcase set",         // 测试用例集的根目录，该目录下可含有多个子目录，每个子目录代表一个测试集
    "testcase-select": ["functional", "performance"],                 // 在 `testcase-base` 所指定的测试集根目录下选取一个或多个需要运行的测试集, 该参数为字符串数组类型
    "num-parallel": 8,                                                // 并发测试的线程数量，根据主机的 CPU 核心数量来选定，即平均每个核心测试一个用例。
    "timeout": 60,                                                    // 超时时间，单位为秒，该参数可以缺省，缺省值为 60 秒。
    "rebuild-compiler": true,                                         // 是否重新构建编译器
    "cache-source": true,                                             // 是否将编译器源代码打包保存到评测记录中，可以缺省，默认值 false (使用 docker 运行则必须为 false)
    "jvm-options": "",                                                // JVM 参数，例如 "-ea"，缺省值为空
    "memory-limit": "256m",                                           // docker 容器内存限制，如超出限制则容器被杀死，缺省值 '256m'
    "opt-options": "",                                                // 编译优化参数，追加到自己的编译器的必需参数之后，例如 "-O2"
    "emit-llvm": false,                                               // 测试后端时顺带输出 LLVM IR
    "run-type": "llvm",                                               // 可选值 "llvm", "qemu", "rpi", "rpi-elf", "interpret"
    "rpi-addresses": ["http://192.168.1.2:9000"],                     // 树莓派 API 地址列表 (如不测试树莓派可留空)
    "log-dir": "logs",                                                // 评测记录存放路径 (可以是相对路径) 缺省值为 `logs`
    "log-dir-host": "logs",                                           // 评测记录在主机上的绝对路径 (使用 docker 运行评测脚本时才需要, 平时不需要填)
}
```

评测方式 `run-type` 参数取值说明

- `llvm`: 测试编译器前端，目标代码为 LLVM IR
- `qemu`: 目标代码为 arm 汇编，使用交叉编译器生成 ELF 并用 qemu 在 x86 机器上测试目标程序
- `rpi`: 目标代码为 arm 汇编，通过 API 在树莓派上链接生成 ELF 并运行
- `rpi-elf`: 目标代码为 arm 汇编，用交叉编译器生成 ELF 并通过 API 在树莓派上执行

参数注意事项：

- `compiler-src`, `compiler-build`, `testcase-base` 三个路径须使用绝对路径。
- 一个测试集 (位于 `testcase-base` 目录下的一个子目录, 通过 `testcase-select` 参数选定)为一个目录，内部由 `.sy`, `.in` 和 `.out` 文件组成。
- 测试自己的编译器，`rebuild-compiler` 参数应为 `true` ；测试往届编译器，此参数为 `false`，此时应将打包好的往届编译器命名为 `compiler.jar` 并置入 `compiler-build` 指向的目录下。
- `log-dir` 和 `log-dir-host` 如果评测程序在 docker 中运行则必须为绝对路径。

其他注意事项：

- 默认的 docker 容器所给的内存限制较小，如果编译、链接或执行所需内存空间较大，请手动指定 `memory-limit` 参数（例如设置为 `4g` 即可获得较大内存空间）
- 容器内存限制 `memory-limit` 和线程数量 `num-parallel` 两参数之间为此消彼长关系，应合理配置以避免系统内存不足
  - 推荐将内存消耗不同的性能测试点分成多个测试集（以及多个配置文件），分开评测
- 推荐关闭 swap，经实测开启 swap 在某些特定条件下会导致文件系统崩溃

配置文件的管理：

一个配置文件代表了一次评测选取的测试点范围以及评测选项。实际使用时往往需要管理多个配置文件，推荐将它们统一放置在一个配置文件目录中，例如 `configs`，并为每个配置文件选取易读的名称。例如:

```
functional.json    functional-qemu.json    functional-llvm.json    performance.json
```

## 运行评测

首先激活 Python 虚拟环境：

```
source .venv/bin/activate
```

然后执行 `main.py` 并将配置文件作为参数传入：

```
python3 -u main.py configs/functional.json
```

## 评测结果

结果默认保存在当前目录下的 `logs` 文件夹 (在配置文件中指定以改变)，每次运行脚本生成一份评测记录，每份记录一个文件夹，名称格式为 "启动时间+进程号"。一份评测记录内包含：

- html 和 json 格式的评测结果摘要
- 如果 `cache-source` 参数为 `true` ，则保存一份压缩的编译器源代码
- 按测试集和测试用例划分的，每个用例一个目录，含有测试用例的源程序、标准输入、期望输出、编译结果、运行输出等

## 在 Docker 中运行本评测机 (供搭建 CI/CD)

根据 `Dockerfile` 构建 docker 镜像。由镜像生成容器时需要使用 `-v` 选项挂载文件:

- 主机上的 `/var/run/docker.sock` 挂载到容器内的相同路径，实现 docker in docker
- 以只读方式挂载 `/etc/localtime` 与 `/etc/timezone` 以同步容器内外系统时间
- 测试用例存放目录和评测结果保存目录
- 配置文件也需挂载到容器

评测脚本启动 java 与 SysY 的 docker 容器用来执行编译器或工具链，需使用 `-v` 选项挂载文件。当评测脚本运行在 docker 容器中时，由于 docker in docker 的 `-v` 只能挂载主机上的目录 (而不是评测脚本所在容器的目录)，因此在编写配置文件时需要注意:

- `compiler-src` 和 `compiler-build` 使用宿主机路径 (绝对路径) 且无需挂载到评测脚本容器中, `cache-source` 必须为 `false` 或不填
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
    -v /etc/timezone:/etc/timezone:ro -v /etc/localtime:/etc/localtime:ro \
    -v ${TESTCASE_BASE}:/testcase/ \
    -v ${LOG_HOST_DIR}:/logs/ \
    -v $(realpath config.json):/app/config.json \
    sysy-test:latest /bin/bash
```

（其中 `${TESTCASE_BASE}` 和 `${LOG_HOST_DIR}` 替换成实际的测试集和测试结果目录，配置文件中 `testcase-base` 为 `/testcase/`, `log-dir` 为 `/logs/` ） 
