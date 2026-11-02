#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini RAG —— 极简文档问答（教学注释版）
=====================================

【这个程序是干什么的】
你给它一篇 markdown 文档，然后用大白话向它提问。它会：
  第 1 步  把文档按标题切成小段            （chunking，切分）
  第 2 步  计算你的问题和每一段有多像，挑出最像的几段（retrieve，检索）
  第 3 步  把挑出的段落和问题拼成一段完整指令（prompt），交给大模型照着资料回答
          （build_prompt，拼装 + ask_llm，调用）
这就是 RAG（检索增强生成）的最小骨架。真实产品比它复杂一万倍，
但拆开来，核心就是这三步。

【怎么跑】
  python rag_demo.py                  # 用同目录的 material.md 当语料
  python rag_demo.py 你的文档.md       # 换你自己的文档
  python rag_demo.py --top-k 3        # 每次检索挑 3 段（默认 4）

【阅读指南】
看不懂的名词（RAG、prompt、bigram、余弦相似度、argparse……），
查同目录的《名词表.md》，每个名词都有详细解释。
代码按"import → 配置 → 第1步切分 → 第2步检索 → 第3步生成 → 主流程"组织，
建议从上往下读一遍，每个函数开头都有大段原理注释。
"""

# ============ 第一部分：导入工具（import）============
# import 的意思是"把别人写好的工具箱搬进来用"。
# Python 自带的"标准库"就像操作系统预装的软件：不用下载，import 就能用。
# 本程序零第三方依赖，全靠下面这几个标准库模块：

import argparse      # 命令行参数解析库。让我们能写 "python rag_demo.py 文档.md --top-k 3"
import os            # 操作系统接口。用来拼文件路径、判断文件存不存在
import re            # 正则表达式。用来按标题切文档、清洗文字
import sys           # 系统级操作。这里只用 sys.exit(1)（报错时退出程序）
from collections import Counter   # 计数器。数每个两字组出现几次，一行搞定词频统计
from math import sqrt             # 平方根。算余弦相似度要开根号

# ============ 第二部分：配置区（想改行为，改这里就够了）============

# API key：调用云端大模型的"钥匙"。没有就留空 —— 程序会自动降级成"手动模式"
# （把拼好的 prompt 打印出来，你自己复制去网页版粘贴）。
# os.environ.get("LLM_API_KEY", "") 的意思是：去系统的环境变量里找 LLM_API_KEY，
# 找到就用找到的值，找不到就用默认值 ""。
# 为什么不把 key 直接写在代码里？因为代码是要公开的，key 写进去等于把钥匙贴大门上。
API_KEY = os.environ.get("LLM_API_KEY", "")

# BASE_URL：大模型服务的网址。默认 DeepSeek（国产、便宜、兼容 OpenAI 的调用格式）。
# 换 ollama 本地模型，就改成 http://localhost:11434/v1
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")

# MODEL：用哪个模型。DeepSeek 的对话模型名叫 deepseek-chat
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

# TOP_K：每次检索最多挑几段材料拼进 prompt。
# 注意是"最多"：相似度为 0 的段落会被过滤掉（见 retrieve 函数最后一行）。
# 段数多 = 材料全但可能掺噪音；段数少 = 精准但可能漏信息。
# 这个权衡没有标准答案，真实项目里是一点一点试出来的。
TOP_K = 4

# MATERIAL：默认语料文件的路径。
# os.path.dirname(os.path.abspath(__file__)) 的意思是"这个 .py 文件自己所在的文件夹"。
# __file__ 是 Python 的内置变量，永远指向"当前这个文件自己的路径"。
# 为什么不直接写 "material.md"？因为如果你在别的目录运行程序
# （比如 python 03-llm-agent/rag_demo.py），相对路径会找不到文件。
# 用 __file__ 定位，就永远指向脚本旁边的语料，从任何目录运行都对。
MATERIAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "material.md")

# ============ 第三部分：RAG 第 1 步 —— 切分 ============

def load_chunks(path):
    """把一篇 markdown 文档按 '## 标题' 切成小段，返回 [{标题, 正文}, ...] 的列表。

    【为什么需要切分】
    大模型的输入长度有限，而且整篇塞给它，它容易"看了后面忘前面"。
    所以先把文档切成小段，提问时只递最相关的几段。
    就像考试允许带小纸条——你不会带整本课本，只抄跟题目相关的段落。

    【为什么按标题切，而不是每 500 字硬切】
    一个 '## 标题' 下的内容通常讲同一件事，切出来的段"主题完整"。
    每 500 字硬切会把一句话拦腰截断，段落语义就残缺了。
    真实项目里，切分策略是门学问：切多大、段与段之间要不要重叠一点，
    直接影响检索质量。
    """
    with open(path, encoding="utf-8") as f:
        # open(路径, encoding="utf-8")：以 UTF-8 编码打开文件。
        # 为什么必须指定 utf-8？Windows 中文系统默认编码是 GBK，
        # 不指定的话读中文 markdown 会乱码甚至直接报错。这是中文开发者的日常坑。
        content = f.read()   # .read()：把整个文件读成一个长字符串

    chunks = []              # 准备一个空列表，用来装切好的段落

    # re.split(r"\n(?=## )", content)：用正则把文档按 "## " 标题切段。
    # 这个正则翻译成白话：找到每一个"换行符，且换行符后面紧跟 ## "的位置，在那里切一刀。
    # (?=## ) 叫"环视"：只检查后面是不是 "## "，但不把它吃掉，
    # 所以标题本身还留在切出的段落里，不会丢。
    parts = re.split(r"\n(?=## )", content)

    for part in parts:       # for 循环：把 parts 里的每一段轮流拿出来处理
        m = re.match(r"##\s*(.+)", part)      # 用正则从段首提取标题
        # re.match：从字符串开头开始匹配。r"##\s*(.+)" 翻译成白话：
        # 开头是 "##"，\s* 是任意空白（空格/tab），(.+) 是标题正文。
        # (.+) 外面的圆括号叫"捕获组"——被圈起来的部分可以单独取出来用。
        if not m:            # 这段开头没有 "##"（比如文档开头的引言），跳过它
            continue        # continue：跳过本轮循环，进入下一段
        title = m.group(1).strip()     # group(1)：取第 1 个捕获组（标题文本）；.strip()：去掉首尾空白
        body = part[m.end():].strip()  # m.end()：标题匹配到的结束位置；从那儿往后就是正文
        if body:             # 只收有正文的段（只有标题没有正文的段没用）
            chunks.append({"title": title, "text": body})   # 把这一段装进列表
    return chunks            # 把切好的所有段交还给调用者


# ============ 第四部分：RAG 第 2 步 —— 检索 ============
# 【检索要解决什么问题】问：这段话和那段话，像不像？
# 计算机不懂"像不像"，它只懂数字。所以要把文字变成数字（向量），再算数字间的距离。

def bigrams(text):
    """把文本切成"字符二元组"（每两个字一组）并统计每个组出现几次。

    【什么是 bigram（二元组）】
    把文字按固定长度滑窗切段，窗长 2 就是 bigram。
    例："大语言模型" -> 大语 / 语言 / 言模 / 模型（4 个两字组）

    【为什么是两个字一组，不是一个字】
    单字信息量太小："模"和"型"单独出现说明不了什么，
    但"模型"这个两字组出现，就基本锁定在说 AI 话题。
    两字组在"保留局部词序"和"抗噪"之间取得了平衡，
    是中文检索里一个经典的零依赖技巧。

    【什么是分词，这里为什么不用】
    英文单词之间有空格，天然分好了词；中文没有。
    专业做法是用 jieba 等分词库，但要额外安装。
    本程序追求零依赖，用 bigram 绕过分词——效果够用，原理可见。
    """
    text = re.sub(r"\s+", "", text)   # \s+：一个或多个空白字符；替换成空字符串 = 删除所有空白
    # 切片 + 计数：i 从 0 数到 len-2，每次取 text[i:i+2]（从第 i 个字开始的两个字）
    # Counter 是 Python 的计数器：给它一串东西，它还你一个"东西 -> 出现次数"的字典
    # 例：Counter(["模型", "模型", "语言"]) -> {"模型": 2, "语言": 1}
    return Counter(text[i:i + 2] for i in range(len(text) - 1))

def cosine(counter_a, counter_b):
    """余弦相似度：比较两个词频向量的"方向"有多接近，结果 0~1，越大越像。

    【算法原理】把每段文字想象成高维空间里的一根箭头：
    - 箭头的每个"维度"是一种两字组
    - 维度的值 = 这个两字组在文中出现的次数
    - 两段文字聊的事越接近，两根箭头的方向越一致
    余弦值就是两根箭头夹角的余弦：1 = 完全同向（最像），0 = 垂直（毫不相干）。

    【公式】cos = (A·B) / (|A| × |B|)
    A·B 是"点积"：两根箭头在共同维度上的乘积之和
    |A| 是"模长"（箭头长度）：所有维度平方和再开根号
    为什么要除以模长？为了"惩罚长文档"——否则文字多的段天然占优势，
    一段长文和任何问题都能扯上关系。除了模长，比的就只是方向。
    """
    common = set(counter_a) & set(counter_b)   # & 是集合交集运算：两边都出现的两字组
    dot = sum(counter_a[k] * counter_b[k] for k in common)   # 点积：共同维度的"次数相乘再求和"
    # 下面两个 sum(v*v) 分别算出两根箭头的平方和，各自开根号得到模长
    norm = sqrt(sum(v * v for v in counter_a.values())) * sqrt(sum(v * v for v in counter_b.values()))
    # 防一手：norm 为 0（比如拿空文本去比）时返回 0，避免"除零"让程序崩溃
    return dot / norm if norm else 0.0

def retrieve(question, chunks, top_k=TOP_K):
    """核心一步：问题 vs 每个文档段算相似度，取分数最高的 top_k 段。

    【真实世界的对应物】企业级 RAG 在这里会换成：
    "向量 embedding 模型 + 向量数据库"——用神经网络把文字变成语义向量，
    毫秒级从百万段落里捞出最相关的。但骨架和这里一模一样：
    都是一个"把问题和高相关段落匹配上"的检索器。今天你写的是它的极简祖先。

    【为什么要按分数排序】prompt 的位置有限，只能挑最像的几段。
    排在最前面的段，模型会"看"得更重点。
    """
    q_vec = bigrams(question)   # 把问题也变成两字组计数器——和段落用同一种"语言"才能比较
    # 列表推导式：对每个段落算一次余弦相似度，得到 [(分数, 段落下标), ...]
    scored = [(cosine(q_vec, bigrams(c["title"] + c["text"])), i) for i, c in enumerate(chunks)]
    # enumerate：遍历列表时同时拿到"下标 i"和"元素 c"，不用自己维护计数器
    # 为什么标题+正文一起参与比较？标题通常是段落的主旨，相当于天然加权
    scored.sort(reverse=True)   # 按分数从高到低排序（reverse=True 表示降序）
    # [:top_k] 取前 top_k 个；if score > 0 把毫不相干的段（0 分）过滤掉
    # 这就是"TOP_K=4 但有时只拼出 2 段"的原因：其他段相似度都是 0，被这里拦下了
    return [(score, chunks[i]) for score, i in scored[:top_k] if score > 0]

# ============ 第五部分：RAG 第 3 步 —— 生成 ============

def build_prompt(question, hits):
    """把检索到的段落 + 问题拼成给大模型的完整指令（prompt）。

    【prompt 三要素】观察这个模板的结构，它包含：
      1. 角色 + 规则（"你是文档问答助手……不要使用资料之外的知识"）
      2. 资料（检索命中的段落，编号列出）
      3. 问题（用户的原话）
    这三块就是 prompt 工程的基本盘：你是谁、看什么材料、回答什么。

    【为什么强调"不要使用资料之外的知识"】
    模型默认会调动它训练时学到的全部知识自由发挥。这句话是刹车：
    逼它只在你给的资料里找答案；资料里没有的，就说"资料里没提到"。
    这一句话，就是"可控回答"和"自由聊天"的分界线。
    """
    # 把 [(分数, 段落), ...] 拼成 "[1] 《标题》\n正文\n\n[2] 《标题》\n正文……" 的长文本
    context = "\n\n".join(
        "[{}] 《{}》\n{}".format(n + 1, h["title"], h["text"]) for n, (score, h) in enumerate(hits)
    )
    # .format() 是字符串模板：把 {} 占位符依次替换成后面的值
    # "\n\n".join(...)：用两个换行把各段资料粘在一起——换行让 prompt 结构清晰，
    # 模型更容易分辨"资料"和"问题"的边界
    return (
        "你是一个文档问答助手。用大白话回答，100 字以内，先给结论，不要使用资料之外的知识。\n"
        "如果资料里找不到答案，就回答'资料里没提到'。\n\n"
        "资料：\n{}\n\n"
        "问题：{}"
    ).format(context, question)

def ask_llm(prompt):
    """有 API key 就调真模型；没有就返回 None（降级为手动模式）。

    【降级设计】没 key 也能完整体验 RAG 的前两步 + 看 prompt 长什么样。
    这是"低成本试错"的典型设计：核心功能不依赖外部服务，
    外部服务只是可选的加速器。
    """
    if not API_KEY:        # 没配 key：直接返回 None，一个字节的网络请求都不发
        return None
    try:
        from openai import OpenAI   # 延迟导入：只在真要调 API 时才加载 openai 包
        # openai 是 OpenAI 官方的 SDK（软件开发工具包）：
        # 它封装了 HTTP 请求的种种细节，让"调大模型"像调用本地函数一样简单。
        # DeepSeek / Kimi / 通义等都兼容这个格式（叫"OpenAI 兼容 API"），
        # 所以同一个 SDK 能打所有家——这就是 base_url 参数存在的意义。
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)   # 客户端：记住钥匙和服务器地址
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            # messages 是"对话历史"列表，role="user" 表示这条是用户说的话
        )
        return resp.choices[0].message.content   # 从响应对象里取出模型回复的文本
    except ImportError:     # 没装 openai 包：提示一句，不崩溃
        print("\n[提示] 还没安装 openai 包。可选：python -m pip install openai")
        return None
    except Exception as e:  # 网络断了 / key 错了 / 欠费了：如实报告，不崩溃
        # try/except 是"异常处理"：把可能出错的代码包起来，出错时执行 except 里的预案，
        # 而不是让程序直接崩掉。type(e).__name__ 取异常的类型名，e 是错误详情。
        print("\n[API 报错] {}: {}".format(type(e).__name__, e))
        print("[提示] 检查 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 三个值。")
        return None

# ============ 第六部分：主流程 ============

def show(hits, prompt):
    """把检索结果和拼好的 prompt 打印到屏幕上。"""
    print("\n" + "─" * 56)     # 分隔线：让屏幕输出有结构，一眼看清三段
    print("第 2 步 · 检索命中（按相关度排序）")
    print("─" * 56)
    for n, (score, h) in enumerate(hits):
        preview = h["text"].replace("\n", " ")[:40]   # 把正文里的换行换成空格，截前 40 字当预览
        print("  [{}] 《{}》  相似度 {:.3f}".format(n + 1, h["title"], score))
        # {:.3f} 是格式化语法：把数字格式化为 3 位小数
        print("      {}……".format(preview))

    print("\n" + "─" * 56)
    print("第 3 步 · 拼给大模型的 prompt（{} 字）".format(len(prompt)))
    print("─" * 56)
    print(prompt)

def main():
    """程序入口：解析参数 -> 加载文档 -> 进入问答循环。"""
    # 【argparse 是干嘛的】解析命令行参数。
    # 你在终端敲的 "python rag_demo.py 文档.md --top-k 3" 到了程序里只是一串字符串，
    # argparse 负责把 "文档.md" 和 3 拆出来，分别递给对应的变量。
    parser = argparse.ArgumentParser(
        description="Mini RAG：极简文档问答（切分 -> 检索 -> 拼 prompt），纯标准库零依赖",
        epilog="示例：python rag_demo.py 我的笔记.md --top-k 3",
    )
    parser.add_argument("doc", nargs="?", default=MATERIAL,
                        help="要问答的 markdown 文档路径（默认：同目录的 material.md）")
    # nargs="?"：这个参数是可选的，不给就用 default 值
    parser.add_argument("--top-k", type=int, default=TOP_K,
                        help="每次检索最多挑几段材料拼进 prompt（默认：{}）".format(TOP_K))
    # "--top-k" 是"长选项"，命令行里写成 --top-k 3；
    # type=int 会自动把字符串 "3" 转成数字 3（命令行传来的一切都是字符串）
    args = parser.parse_args()   # 正式解析，结果都装在 args 里

    if not os.path.isfile(args.doc):   # os.path.isfile：这个路径是个文件吗？
        print("找不到文件：{}".format(args.doc))
        sys.exit(1)     # 异常退出。约定：0 = 正常结束，非 0 = 出错，别的程序可以靠这个判断成败

    chunks = load_chunks(args.doc)   # 第 1 步：切分文档
    print("Mini RAG 已就绪：{} 个文档段来自 {}".format(len(chunks), args.doc))
    if API_KEY:
        print("已配置 API，直接跑真问答。")
    else:
        print("未配置 API key —— 前两步照常跑，prompt 拼好后请贴到任意")
        print("大模型网页版（DeepSeek / 通义 / Kimi 都行），那就是一次完整的 RAG 问答。")
    print("输入问题回车，输入 q 退出。\n")

    while True:      # while True：无限循环，直到用户输入 q 时 break 出去
        try:
            q = input("问：").strip()   # input()：在终端等待用户敲一行字；.strip() 去掉首尾空格
        except (EOFError, KeyboardInterrupt):   # Ctrl+C / Ctrl+D 也允许体面退出
            print("\n再见。")
            break
        if not q or q.lower() == "q":   # 空输入或 q：退出循环
            print("再见。")
            break

        hits = retrieve(q, chunks, top_k=args.top_k)   # 第 2 步：检索
        if not hits:
            print("  没有检索到任何相关段落——换个问法试试（关键词重叠太少）。\n")
            continue     # 没命中就重新问，不用拼 prompt
        prompt = build_prompt(q, hits)   # 第 3 步：拼 prompt
        show(hits, prompt)               # 把检索结果和 prompt 打印出来

        answer = ask_llm(prompt)         # 尝试调 API（没 key 就返回 None）
        if answer:
            print("\n" + "─" * 56)
            print("模型的回答")
            print("─" * 56)
            print(answer)
        else:
            print("\n[手动模式] 复制上面的 prompt，贴进任意大模型网页版，对比它")
            print("            '根据资料回答'和'自由发挥回答'的差别——这就是 RAG 的价值。\n")

if __name__ == "__main__":
    # 【这行是什么意思】"当这个文件被直接运行时，才执行 main()"
    # 如果别的程序 import 这个文件（把它当工具库引用），main() 不会自动跑。
    # 几乎每个 Python 脚本都该有这行，是工程惯例。
    main()
