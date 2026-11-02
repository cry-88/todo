"""
随机笑话 API —— D2 后端开发体验 demo（教学注释版）
==================================================

后端最核心的心智模型，就一条线：

    浏览器发请求(request) → 服务器按路由表找到处理函数 → 返回响应(response)

你今天要感受的就是这条线。终端里每跳出一行日志，就是有一个请求流过。

【这个文件怎么读】按"请求流过"的顺序读：
    import（工具）→ 数据（笑话存哪）→ 路由表（什么网址谁处理）→ 启动（点火）

【怎么跑】在 02-backend 目录下：
    venv/Scripts/python app.py
然后浏览器打开 http://localhost:5050
想停止：终端里按 Ctrl+C
【看不懂的词】查《名词表.md》。
"""

# ============ import：把工具箱搬进来 ============
# flask 是第三方 Web 框架（要 pip install）——帮你把 HTTP 协议的脏活都包了，
# 你只需要写"什么网址返回什么"。
from flask import (
    Flask,               # 应用对象：整个服务器的核心
    jsonify,             # 把 Python 字典/列表变成 JSON 响应
    send_from_directory, # 把服务器上的一个文件发给浏览器（发 HTML 页面用）
    request,             # 拿到本次请求的一切信息（身体里的数据、参数……）
)
import random            # 随机数模块：随机挑一条笑话用
import os                # 路径/文件判断：jokes.json 放哪、在不在
import json              # JSON 读写：数据落盘、读盘

# Flask(__name__) 创建应用对象。__name__ 是 Python 内置变量（当前模块名），
# Flask 靠它定位资源文件——照抄这行就行，不用深究。
app = Flask(__name__)

# 让 JSON 里的中文直接显示，不用 \uXXXX 转义（F12 Network 里看原始数据更直观）。
# 不加这行，中文会变成 "\u4f60\u597d" 这种天书。
app.json.ensure_ascii = False

# ---------- 数据：文件持久化 ----------
# 种子数据：代码里写死的 14 条。第一次运行时写入 jokes.json，
# 之后 jokes.json 才是真相——投稿不再活在内存里，重启服务器也不会丢。
# （D5 数据库日，我们会把文件换成 SQLite，体会"十万条数据还要秒查"的场合）

# os.path.dirname(os.path.abspath(__file__)) = 这个 app.py 自己所在的文件夹。
# 用它拼路径，而不是写死 "jokes.json"——这样从任何目录启动都能找到数据文件。
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jokes.json")

# 每条笑话是一个字典：id（编号）/ setup（铺垫）/ punchline（包袱）。
# 字典用 {} 包，键值对之间逗号分隔——这是 JSON 的近亲，JSON 就是从 JS 字典演化来的。
SEED_JOKES = [
    {"id": 1, "setup": "程序员最讨厌的两件事", "punchline": "写文档，和别人不写文档"},
    {"id": 2, "setup": "为什么程序员总是分不清万圣节和圣诞节", "punchline": "因为 Oct 31 == Dec 25（八进制的 31 就是十进制的 25）"},
    {"id": 3, "setup": "一个 SQL 语句走进酒吧，走到两张桌子前", "punchline": "它问：我能 JOIN 你们吗？"},
    {"id": 4, "setup": "为什么程序员喜欢暗色模式", "punchline": "因为光会吸引 bug"},
    {"id": 5, "setup": "妻子让程序员买东西：买 6 个鸡蛋，如果有西红柿，就买 10 个", "punchline": "结果他买了 10 个鸡蛋"},
    {"id": 6, "setup": "什么是调试代码", "punchline": "在黑暗中打猎，而猎物还是隐形的"},
    {"id": 7, "setup": "为什么程序员不爱出门？", "punchline": "外面的环境没有IDE自动补全"},
    {"id": 8, "setup": "算法和数据结构去相亲，为什么黄了？", "punchline": "算法说它时间复杂度O(1)，数据结构说它空间不够存感情"},
    {"id": 9, "setup": "程序员去钓鱼，钓上来什么最开心？", "punchline": "不是鱼，是没有空指针的浮标"},
    {"id": 10, "setup": "递归为什么容易抑郁？", "punchline": "它总是找不到终止条件"},
    {"id": 11, "setup": "数组和链表去逛街，谁走得更快？", "punchline": "数组，它可以随机访问，链表只能一步一步挪"},
    {"id": 12, "setup": "为什么C++程序员很难交到朋友？", "punchline": "动不动就抛出异常"},
    {"id": 13, "setup": "Git 最害怕什么？", "punchline": "强制覆盖，直接丢掉所有回忆"},
    {"id": 14, "setup": "浮点数为什么不适合谈恋爱？", "punchline": "看起来相等，实际上并不相等"},

]


def save_jokes(joke_list):
    """把整个笑话列表写进 jokes.json（ensure_ascii=False 让中文直接可读）

    with open(...) 是"上下文管理器"：块结束自动关文件，不怕忘。
    "w" = write 模式（整个文件重写）；indent=2 让 JSON 有缩进，人看得舒服。
    """
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(joke_list, f, ensure_ascii=False, indent=2)


def load_jokes():
    """启动时加载：jokes.json 存在就从文件读（含以前的所有投稿）；否则用种子并落盘"""
    if os.path.exists(DATA_FILE):
        # "r" 读模式是默认的，不写也行；这里显式写出来是习惯
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)   # json.load（从文件）vs json.loads（从字符串），别混
    # 第一次运行：把种子写进去，下次启动读到的就是它
    save_jokes(SEED_JOKES)
    return list(SEED_JOKES)   # list(...) 拷贝一份，防止 SEED_JOKES 被后续代码改坏


# 模块级代码：import 本文件时就会执行到这里——这就是"服务器启动时笑话已在内存"
jokes = load_jokes()

# ---------- 页面 ----------

# @app.route("/") 是"路由装饰器"：把下面的函数注册成"网址 / 的处理器"。
# 装饰器 = 给函数贴个标签，Flask 启动时扫描所有标签，生成路由表。
@app.route("/")
def home():
    # 直接返回一段 HTML 字符串——最简单的情况，Flask 允许你这么干
    return """
    <h1>程序员笑话小站</h1>
    <p>接口：/api/joke/random 随机笑话</p>
    <p>接口：/api/joke/count 笑话总数</p>
    <p>接口：/api/jokes 全部笑话</p>
    <p>接口：/api/joke/数字id 查看单条笑话</p>
    <p>接口：POST /api/joke 提交新笑话（去 /play 页面提交）</p>
    <p><a href="/play">去前端页面玩</a></p>
    """



@app.route("/play")
def play():
    # 把同目录下的 client.html 发给浏览器。
    # 浏览器拿到的就是 D1 那种前端页面，它再回头调下面的 API——前后端分离的最小形态
    here = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(here, "client.html")


# ---------- 接口（API）----------
# @app.route(...) 就是"路由表"：什么网址，交给哪个函数处理

@app.route("/api/joke/random")
def random_joke():
    # random.choice：从列表里随机挑一个
    joke = random.choice(jokes)
    # jsonify 把 Python 字典变成 JSON——前后端之间运数据的标准格式
    return jsonify(joke)

@app.route("/api/joke/count")
def joke_count():
    # len() 数列表长度。注意这里返回的也是"字典包一层"——前端解析更方便
    return jsonify({"count": len(jokes)})

@app.route("/api/jokes")
def all_jokes():
    return jsonify({"count": len(jokes), "jokes": jokes})


@app.route("/api/joke/<int:joke_id>")
def one_joke(joke_id):
    # 网址里的 <int:joke_id> 会作为参数传进来，比如 /api/joke/3 → joke_id=3。
    # int 是类型过滤：/api/joke/abc 这种直接 404，到不了函数里
    for joke in jokes:   # 遍历列表找 id 匹配的——数据量小时够用，大了就是 D5 的课题
        if joke["id"] == joke_id:
            return jsonify(joke)
    # 找不到要如实说——404 是"没有这个资源"的官方回答。
    # return 两个值 = (响应体, 状态码)，Flask 认这个写法
    return jsonify({"error": f"没有 id 为 {joke_id} 的笑话"}), 404


# ---------- 投稿新笑话（POST）----------
# GET 是"要数据"（数据放在网址里），POST 是"送数据"（数据放在请求身体里）。
# 一个路由可以声明只接 POST：methods=["POST"]。默认只接 GET。
@app.route("/api/joke", methods=["POST"])
def add_joke():
    # 从请求身体里取出浏览器发来的 JSON，变成 Python 字典。
    # silent=True：送来的不是合法 JSON 时返回 None 而不是直接崩；
    # "or {}"：None 时兜底成空字典，下面 .get 才不会报错
    data = request.get_json(silent=True) or {}
    setup = data.get("setup", "").strip()      # .get(key, 默认值)：key 不存在时给默认值
    punchline = data.get("punchline", "").strip()
    # 后端永远不信任前端送来的东西——空的、缺的，都要在这里挡住。
    # 前端校验是"为了体验"，后端校验是"为了安全"，两道都要有。
    if not setup or not punchline:
        # 400 = "你请求有问题"（客户端错误），和 404（找不到）区分开
        return jsonify({"error": "setup 和 punchline 都不能为空"}), 400
    # id 接着现有最大的往下编（default=0 是防空列表的保险——
    # max() 空序列会报错，加 default 就不报了）
    new_id = max((j["id"] for j in jokes), default=0) + 1
    joke = {"id": new_id, "setup": setup, "punchline": punchline}
    jokes.append(joke)
    save_jokes(jokes)   # 落盘：从此这条投稿永久保存，重启也不丢
    # 201 = "创建成功"，比 200 更精确的状态码。状态码是服务器和客户端的"暗语"
    return jsonify(joke), 201


# ---------- 启动 ----------
if __name__ == "__main__":
    # 这行的意思："直接运行本文件时才启动服务器；被别人 import 时不启动"
    # （第 4 步写 pytest 测试时就是 import 它，所以必须这么写）
    #
    # __name__ 是 Python 给每个模块贴的名字：直接运行时它等于 "__main__"，
    # 被 import 时等于模块名（"app"）。
    #
    # debug=True：改代码保存后自动重启；页面出错时显示详细原因（开发期专用，
    # 上线必须关——错误详情会泄露代码结构）
    app.run(debug=True, port=5050)   # port=5050：换端口防冲突；5000 常被占用
