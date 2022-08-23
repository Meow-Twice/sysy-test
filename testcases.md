# 测试用例存储说明

## 文件规则

每个测试点必须包含一个 `.sy` 源代码文件和一个 `.out` 输出文件，如果该用例有标准输入则需要提供一个 `.in` 输入文件。两个或三个文件均以测试用例名称命名。不同测试用例之间不能重名。

示例：两个测试点，名称分别为 `testfile1` 和 `testfile2` ，其中 `testfile2` 有输入，则按以下方式组织文件

```
testfile1.sy
testfile1.out
testfile2.sy
testfile2.in
testfile2.out
```

测试用例的分组：每组一个子目录，子目录内的用例组织结构同上。同一个分组内的测试点之间不能重名。

示例：测试用例分 `simple` 和 `float` 两个组，每个组有若干测试用例

```
simple/
|---testfile1.sy
|---testfile1.out
|---testfile2.sy
|---testfile2.in
|---testfile2.out
float/
|---float1.sy
|---float1.out
|---float2.sy
|---float2.in
|---float2.out
```

## 输出文件

测试用例的 `.out` 文件格式与官方相同，除标准输出内容外，还应在最后一行补上 `main` 函数的返回值。`main` 函数的返回值范围只能在 `0-255` 之间。

输出文件的最后一行为 `main` 函数的返回值，且整个文件以空行结尾（在 VS Code 中打开输出文件，主函数返回值后应显示一个空行）。

生成输出文件的参考终端命令:

```shell
# 执行 ELF 文件，重定向输入输出
./testfile < testfile.in > testfile.out
# 获取上一条命令执行的返回值
r=$?
# 如输出文件不以空行结尾，补充换行符
if [ ! -z "$(tail -c 1 testfile.out)" ]; then
    echo >> testfile.out
fi
# 追加执行返回值到输出文件
echo $r >> testfile.out
```

## 有关换行符的提示

Windows 系统文本文件的默认换行符为 `\r\n` ，而 Linux 系统的文本文件默认换行符为 `\n` 。为了避免可能因 Windows 中"回车"符号 `\r` 在 Linux 引起难以预测的问题，强烈推荐使用 Linux 系统编写及执行测试用例。

如果使用 Windows 系统，可以使用 VS Code 打开用例输入输出文件，在右下角查看当前文件的换行符，如果为 `CRLF` 则将其调整为 `LF` 。
