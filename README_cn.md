# BibTeX Reference Optimizer

一个使用DBLP API优化BibTeX引用文件的Python工具。

## 功能

- 读取BibTeX文件中的论文条目
- 使用DBLP API根据论文标题搜索获取标准化的出版信息
- 提取作者、标题、会议/期刊名、页码、卷号、期号等信息
- 生成优化后的BibTeX文件
- 保持原有的引用键(cite key)不变
- 报告处理失败的条目

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python refine_bib.py
```

这将读取`ref_input.bib`文件并生成`ref_output.bib`文件。

### 指定输入输出文件

```bash
python refine_bib.py input.bib output.bib
```

### 设置API请求间隔

```bash
python refine_bib.py --delay 10.0
```

默认请求间隔为10秒，避免过于频繁的API调用。

## 参数说明

- `input_file`: 输入的BibTeX文件路径（默认：ref_input.bib）
- `output_file`: 输出的BibTeX文件路径（默认：ref_output.bib）
- `--delay`: API请求间隔时间，单位秒（默认：10.0秒）

## 示例

项目包含一个示例`ref_input.bib`文件，包含几个常见的机器学习论文引用。运行工具后，会生成优化后的`ref_output.bib`文件。

## 注意事项

1. 工具会根据论文标题在DBLP中搜索，如果标题不准确可能找不到匹配结果
2. 为避免过度请求DBLP服务器，建议保持合理的请求间隔
3. 失败的条目将在控制台输出，原始信息会保留在输出文件中

## DBLP API

本工具使用DBLP公开的搜索API：
- API端点：https://dblp.org/search/publ/api
