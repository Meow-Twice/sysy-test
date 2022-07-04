# 编译测试脚本

目前已支持对编译器前端 LLVM IR 的测试。

## 环境建立说明

（以下命令需要在该工程所在目录下执行）

### Python 虚拟环境

```shell
python3 -m virtualenv .venv     # 建立 Python 虚拟环境 (需要使用 virtualenv 模块)
source .venv/bin/activate       # 激活虚拟环境
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple # 安装依赖模块
```

### 配置文件

在当前目录创建 `config.json` (如采用其他文件名，需修改 `main.py` 中的 `CONFIG_FILE` 常量为相应文件名)，格式如下:

```json
{
    "compiler-src": "path to your compiler source code",
    "compiler-build": "path to store build output of your compiler",
    "testcase-path": "path to testcase set",
    "num-parallel": 8
}
```

其中:

- `compiler-src`: 编译器的源代码目录 (Java 工程目录下的 `src` 目录)
- `compiler-build`: 存放编译器的 `.class` 以及 `.jar` 的目录 (例如 Java 工程目录下的 `build` 目录)
- `testcase-path`: 测试用例集的所在目录 (必须指定是功能用例集还是性能用例集，例如 `compiler-testcase/functional`，目录内只能是由 `.sy`, `.in` 和 `.out` 文件组成)
- `num-parallel`: 并发测试的线程数量，根据主机的 CPU 核心数量来选定，即平均每个核心测试一个用例。

以上三个路径均为**绝对路径**。

### 必需的 docker 镜像

- Java JDK 镜像: `docker pull openjdk:15-alpine`
- SysY 测试镜像: 基于 GitHub 仓库构建, `git clone git@github.com:dhy2000/sysy-docker.git; cd sysy-docker; ./docker-build.sh` 。镜像名称为 `sysy:latest` 。

## 运行方法

完成上述所有准备工作后，在激活虚拟环境后执行 `python3 -u main.py` 即可开始测试。测试结果位于 `logs` 目录中。