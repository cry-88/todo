"""
随机笑话 API —— D2 后端开发体验 demo
====================================

后端最核心的心智模型，就一条线：

    浏览器发请求(request) → 服务器按路由表找到处理函数 → 返回响应(response)

你今天要感受的就是这条线。终端里每跳出一行日志，就是有一个请求流过。

运行方式（在 02-backend 目录下）：
    venv/Scripts/python app.py
然后浏览器打开 http://localhost:5000
想停止：终端里按 Ctrl+C
"""

from flask import Flask, jsonify, send_from_directory
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
]

# ---------- 页面 ----------

@app.route("/")
def home():
    # 后端不只是返回数据，也可以返回网页（早年的网站都是这么干的）
    return "<h1>笑话 API 跑起来了</h1><p>试试这些地址：</p><ul><li>/api/joke/random 随机一条</li><li>/api/jokes 全部</li><li>/play 网页版</li></ul>"


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


# ---------- 启动 ----------
if __name__ == "__main__":
    # 这行的意思："直接运行本文件时才启动服务器；被别人 import 时不启动"
    # （第 4 步写 pytest 测试时就是 import 它，所以必须这么写）
    #
    # debug=True：改代码保存后自动重启；页面出错时显示详细原因（开发期专用）
    app.run(debug=True, port=5000)
