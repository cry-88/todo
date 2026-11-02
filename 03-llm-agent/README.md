# mini-rag

**130 行 Python 标准库实现的最小 RAG（检索增强生成）**：不装任何第三方包，跑通「切分 → 检索 → 拼 prompt」的完整骨架，并亲手验证 RAG 的价值链。

## 效果

```
$ python rag_demo.py
Mini RAG 已就绪：7 个文档段来自 material.md

问：我体测多少分？

── 第 2 步 · 检索命中 ──
  [1] 《这周我成功体测过80分了》  相似度 0.075
  [2] 《为什么需要提示词》  相似度 0.023

── 第 3 步 · 拼给大模型的 prompt ──
你是一个文档问答助手。用大白话回答，100 字以内，先给结论，不要使用资料之外的知识。
资料：
[1] 《这周我成功体测过80分了》...
问题：我体测多少分？
```

模型照资料答出「80 分」——而同样的问题**不带资料**提问，模型一无所知。**这个落差，就是 RAG 存在的全部理由。**

## 快速开始

需要 Python 3.8+，**零第三方依赖**：

```bash
python rag_demo.py                  # 用自带语料（一篇讲 LLM/RAG 的科普文）
python rag_demo.py 你的文档.md       # 问答你自己的 markdown 文档
python rag_demo.py --top-k 3        # 调整每次检索的段数
python rag_demo.py --help           # 查看全部参数
```

## RAG 三步，代码在哪

| 步骤 | 函数 | 做什么 |
|---|---|---|
| 切分 chunking | `load_chunks()` | 按 markdown 标题把长文档切成小段 |
| 检索 retrieve | `retrieve()` / `bigrams()` / `cosine()` | 问题与每段算相似度，取最高的几段 |
| 生成 generate | `build_prompt()` / `ask_llm()` | 段落 + 问题拼成 prompt，交给大模型 |

检索用的技巧是**字符二元组余弦相似度**：中文没有空格分词，`大语言模型` 切成 `大语/语言/言模/模型` 四个两字组，零依赖实现中文匹配。真实世界的 RAG 在这里会换成「向量 embedding + 向量数据库」，但骨架一模一样——都是一个「把问题和高相关段落匹配上」的检索器。

## 复现对比实验（RAG 的价值链）

1. 跑 `python rag_demo.py`，问一个语料里的问题，复制屏幕上拼好的 prompt
2. **A 组**：把 prompt 贴进任意大模型（DeepSeek / Kimi / 通义），拿回答
3. **B 组**：新开一个对话，只发问题本身，不带资料
4. 对比：A 的每句话都有出处；B 只能凭常识猜

## 接入真 API（可选）

默认手动模式（复制 prompt 去网页版）。想直接出回答：

```bash
pip install openai
export LLM_API_KEY="你的key"                       # 任一 OpenAI 兼容 API
export LLM_BASE_URL="https://api.deepseek.com"     # 例如 DeepSeek
export LLM_MODEL="deepseek-chat"
python rag_demo.py
```

本地模型同理：装 [ollama](https://ollama.com) 后把 `LLM_BASE_URL` 改成 `http://localhost:11434/v1`、`LLM_MODEL` 改成本地模型名即可，代码一行不用动。

## 已知限制（诚实清单）

- **检索是乞丐版**：bigram 余弦没有语义理解，「体测」和「体育考试」在它眼里毫不相干——工程上会换 embedding 模型
- **top_k 会掺噪音**：段数调大可能把弱相关段落（相似度 0.02 那种）拼进 prompt，稀释真正有用的材料
- **无重排、无评估**：真实 RAG 还有 rerank 环节和回答质量评估，这里全部省略
- **prompt 模板是写死的**：换任务要自己改 `build_prompt()`

## 背景

14 天计算机方向体验计划 D3（LLM / Agent 方向）的体验产物——不求学会 RAG，只求用最低成本「看见」它的骨架，并采集「设计 AI 流程」的真实体感。
