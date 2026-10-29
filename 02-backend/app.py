"""
随机笑话 API —— D2 后端开发体验 demo
====================================

后端最核心的心智模型，就一条线：

    浏览器发请求(request) → 服务器按路由表找到处理函数 → 返回响应(response)

你今天要感受的就是这条线。终端里每跳出一行日志，就是有一个请求流过。

运行方式（在 02-backend 目录下）：
    venv/Scripts/python app.py
然后浏览器打开 http://localhost:5050
想停止：终端里按 Ctrl+C
"""

from flask import Flask, jsonify, send_from_directory, request
import random
import os

# Flask 应用对象——整个服务器的核心就是这个 app
app = Flask(__name__)

# 让 JSON 里的中文直接显示，不用 \uXXXX 转义（F12 Network 里看原始数据更直观）
app.json.ensure_ascii = False

# ---------- "数据库"：内存里的一张表 ----------
# 现在数据放在这个列表里，服务器一重启就全丢。
# D5 数据库体验日，我们会把它换成真正的 SQLite——先记住这个"待办"。
jokes = [
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

# ---------- 页面 ----------

@app.route("/")
def home():
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
    # 把同目录下的 client.html 发给浏览器
    here = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(here, "client.html")


# ---------- 接口（API）----------
# @app.route(...) 就是"路由表"：什么网址，交给哪个函数处理

@app.route("/api/joke/random")
def random_joke():
    joke = random.choice(jokes)
    # jsonify 把 Python 字典变成 JSON——前后端之间运数据的标准格式
    return jsonify(joke)

@app.route("/api/joke/count")
def joke_count():
    return jsonify({"count": len(jokes)})

@app.route("/api/jokes")
def all_jokes():
    return jsonify({"count": len(jokes), "jokes": jokes})


@app.route("/api/joke/<int:joke_id>")
def one_joke(joke_id):
    # 网址里的 <int:joke_id> 会作为参数传进来，比如 /api/joke/3 → joke_id=3
    for joke in jokes:
        if joke["id"] == joke_id:
            return jsonify(joke)
    # 找不到要如实说——404 是"没有这个资源"的官方回答
    return jsonify({"error": f"没有 id 为 {joke_id} 的笑话"}), 404


# ---------- 投稿新笑话（POST）----------
# GET 是"要数据"（数据放在网址里），POST 是"送数据"（数据放在请求身体里）。
# 一个路由可以声明只接 POST：methods=["POST"]
@app.route("/api/joke", methods=["POST"])
def add_joke():
    # 从请求身体里取出浏览器发来的 JSON，变成 Python 字典
    # silent=True：送来的不是合法 JSON 时返回 None 而不是直接崩
    data = request.get_json(silent=True) or {}
    setup = data.get("setup", "").strip()
    punchline = data.get("punchline", "").strip()
    # 后端永远不信任前端送来的东西——空的、缺的，都要在这里挡住
    if not setup or not punchline:
        return jsonify({"error": "setup 和 punchline 都不能为空"}), 400
    # id 接着现有最大的往下编（default=0 是防空列表的保险）
    new_id = max((j["id"] for j in jokes), default=0) + 1
    joke = {"id": new_id, "setup": setup, "punchline": punchline}
    jokes.append(joke)
    # 201 = "创建成功"，比 200 更精确的状态码
    return jsonify(joke), 201


# ---------- 启动 ----------
if __name__ == "__main__":
    # 这行的意思："直接运行本文件时才启动服务器；被别人 import 时不启动"
    # （第 4 步写 pytest 测试时就是 import 它，所以必须这么写）
    #
    # debug=True：改代码保存后自动重启；页面出错时显示详细原因（开发期专用）
    app.run(debug=True, port=5050)
