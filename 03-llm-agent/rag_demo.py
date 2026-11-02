#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini RAG —— 极简文档问答
=========================
三段式，对应今天要建立的三个根概念：

  1. 切分(chunking) ：把长文档按标题切成小段      -> load_chunks()
  2. 检索(retrieve) ：提问 -> 找出最相关的几段      -> retrieve()
  3. 生成(generate) ：把这几段拼进 prompt          -> build_prompt()

本文件只用 Python 标准库，不装任何第三方包也能跑。
配置了 API key 就跑真问答；没配置也能完整体验前两段 + 看拼接结果。

运行：
    python rag_demo.py
"""

import argparse
import os
import re
import sys
from collections import Counter
from math import sqrt

# ---------------- 配置区（今天唯一需要动手改的地方之一） ----------------

API_KEY = os.environ.get("LLM_API_KEY", "")          # 你的 API key，没有就留空
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")  # 国产 API 多兼容 OpenAI 格式
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
TOP_K = 4          # 每次检索挑几段材料拼进 prompt
MATERIAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "material.md")

# ---------------- 第 1 段：切分 ----------------

def load_chunks(path):
    """按 markdown 的 '## 标题' 把文档切成小段。

    返回列表，每个元素是 {'title': 节标题, 'text': 正文}。
    为什么按标题切？因为一个标题下的内容通常讲同一件事，
    检索时"整段命中"比"半句话命中"更利于模型理解上下文。
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    chunks = []
    # 用正则按 '## ' 开头的行切分。re.split 会把标题本身留在切分结果里。
    parts = re.split(r"\n(?=## )", content)
    for part in parts:
        m = re.match(r"##\s*(.+)", part)
        if not m:
            continue
        title = m.group(1).strip()
        body = part[m.end():].strip()
        if body:
            chunks.append({"title": title, "text": body})
    return chunks

# ---------------- 第 2 段：检索 ----------------

def bigrams(text):
    """把文本切成"字符二元组"（每两个字一组）。

    中文没有空格分词，jieba 等分词库要额外安装。
    bigram 是一个零依赖的替代技巧：'大语言模型' -> ['大语','语言','言模','模型']，
    重叠的两字组天然携带局部词序信息，用来算相似度足够好用。
    """
    text = re.sub(r"\s+", "", text)  # 去掉所有空白字符
    return Counter(text[i:i + 2] for i in range(len(text) - 1))

def cosine(counter_a, counter_b):
    """两个词频向量的余弦相似度，范围 0~1，越大越像。"""
    common = set(counter_a) & set(counter_b)
    dot = sum(counter_a[k] * counter_b[k] for k in common)
    norm = sqrt(sum(v * v for v in counter_a.values())) * sqrt(sum(v * v for v in counter_b.values()))
    return dot / norm if norm else 0.0

def retrieve(question, chunks, top_k=TOP_K):
    """核心一步：问题 vs 每个文档段，算相似度，取最高的 top_k 段。

    真实世界的 RAG 在这里会换成"向量 embedding + 向量数据库"，
    但骨架完全一样：都是一个"把问题和高相关段落匹配上"的检索器。
    """
    q_vec = bigrams(question)
    scored = [(cosine(q_vec, bigrams(c["title"] + c["text"])), i) for i, c in enumerate(chunks)]
    scored.sort(reverse=True)
    return [(score, chunks[i]) for score, i in scored[:top_k] if score > 0]

# ---------------- 第 3 段：生成 ----------------

def build_prompt(question, hits):
    """把检索到的段落 + 问题拼成给大模型的 prompt。

    注意这个模板的三要素：角色/任务、资料、问题。
    你改动这里的一句话，模型的回答就可能变化——这就是 prompt 工程。
    """
    context = "\n\n".join(
        "[{}] 《{}》\n{}".format(n + 1, h["title"], h["text"]) for n, (score, h) in enumerate(hits)
    )
    return (
        "你是一个文档问答助手。用大白话回答，100 字以内，先给结论，不要使用资料之外的知识。\n"
        "如果资料里找不到答案，就回答'资料里没提到'。\n\n"
        "资料：\n{}\n\n"
        "问题：{}"
    ).format(context, question)

def ask_llm(prompt):
    """有 API key 就调真模型；没有就返回 None（降级为手动模式）。"""
    if not API_KEY:
        return None
    try:
        from openai import OpenAI  # 只有真调 API 才需要这个包
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
    except ImportError:
        print("\n[提示] 还没安装 openai 包。可选：python -m pip install openai")
        return None
    except Exception as e:
        print("\n[API 报错] {}: {}".format(type(e).__name__, e))
        print("[提示] 检查 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 三个值。")
        return None

# ---------------- 主流程 ----------------

def show(hits, prompt):
    print("\n" + "─" * 56)
    print("第 2 步 · 检索命中（按相关度排序）")
    print("─" * 56)
    for n, (score, h) in enumerate(hits):
        preview = h["text"].replace("\n", " ")[:40]
        print("  [{}] 《{}》  相似度 {:.3f}".format(n + 1, h["title"], score))
        print("      {}……".format(preview))

    print("\n" + "─" * 56)
    print("第 3 步 · 拼给大模型的 prompt（{长度} 字）".format(长度=len(prompt)))
    print("─" * 56)
    print(prompt)

def main():
    parser = argparse.ArgumentParser(
        description="Mini RAG：极简文档问答（切分 -> 检索 -> 拼 prompt），纯标准库零依赖",
        epilog="示例：python rag_demo.py 我的笔记.md --top-k 3",
    )
    parser.add_argument("doc", nargs="?", default=MATERIAL,
                        help="要问答的 markdown 文档路径（默认：同目录的 material.md）")
    parser.add_argument("--top-k", type=int, default=TOP_K,
                        help="每次检索最多挑几段材料拼进 prompt（默认：{}）".format(TOP_K))
    args = parser.parse_args()

    if not os.path.isfile(args.doc):
        print("找不到文件：{}".format(args.doc))
        sys.exit(1)

    chunks = load_chunks(args.doc)
    print("Mini RAG 已就绪：{} 个文档段来自 {}".format(len(chunks), args.doc))
    if API_KEY:
        print("已配置 API，直接跑真问答。")
    else:
        print("未配置 API key —— 前两步照常跑，prompt 拼好后请贴到任意")
        print("大模型网页版（DeepSeek / 通义 / Kimi 都行），那就是一次完整的 RAG 问答。")
    print("输入问题回车，输入 q 退出。\n")

    while True:
        try:
            q = input("问：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not q or q.lower() == "q":
            print("再见。")
            break

        hits = retrieve(q, chunks, top_k=args.top_k)
        if not hits:
            print("  没有检索到任何相关段落——换个问法试试（关键词重叠太少）。\n")
            continue

        prompt = build_prompt(q, hits)
        show(hits, prompt)

        answer = ask_llm(prompt)
        if answer:
            print("\n" + "─" * 56)
            print("模型的回答")
            print("─" * 56)
            print(answer)
        else:
            print("\n[手动模式] 复制上面的 prompt，贴进任意大模型网页版，对比它")
            print("            '根据资料回答'和'自由发挥回答'的差别——这就是 RAG 的价值。\n")

if __name__ == "__main__":
    main()
