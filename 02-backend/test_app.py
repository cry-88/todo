"""
笑话 API 的 pytest 测试（教学注释版）
====================================

测试是"和代码逻辑对话"：你定好规则，让机器反复验证它。
以后每改一次 app.py，跑一遍测试就知道有没有改坏别的地方——这是专业开发的日常。

【pytest 是什么】Python 最流行的测试框架。
   规则极简：文件名叫 test_*.py，函数名叫 test_*，函数里用 assert 断言。
   pytest 自动找出所有 test_ 开头的函数，挨个跑，报告谁过谁挂。

【怎么跑】在 02-backend 目录下：
    venv/Scripts/pytest -v

【本文件的 5 个测试】随机接口 / 总数 / 404 / POST 投稿成功 / POST 空内容被挡。
   注意 test_joke_count 用 == len(jokes) 而不是写死数字——笑话库再增长，测试也不会失效。
   【这是什么思想】测试"关系"而不是"快照"：数字会变，关系不变。
"""
# 能 import app 成功，靠的就是 app.py 最后的 if __name__ == "__main__" 守卫——
# 被 import 时服务器不会启动，只会安静地把 app 对象交出来
from app import app, jokes

# app.test_client() = "假浏览器"：不用真开服务器、不用真发 HTTP，
# 直接在内存里调用接口。快，且不占端口——测试的标准做法
client = app.test_client()


def test_random_joke_ok():
    """随机接口应该返回 200，并且 body 里有 setup 和 punchline"""
    # client.get(网址)：模拟一次 GET 请求，返回"响应对象"（和浏览器拿到的一样）
    res = client.get("/api/joke/random")
    # assert = 断言：条件不成立就当场报错，测试挂。
    # 测试的哲学：不猜，只断。每个关键约定都写成 assert
    assert res.status_code == 200
    # get_json()：把响应里的 JSON 文本解析成 Python 字典
    data = res.get_json()
    assert "setup" in data      # in 对字典是查"键存不存在"
    assert "punchline" in data


def test_joke_count():
    """总数接口应该返回 count=当前笑话数（用 len(jokes) 而不是写死数字，永不过期）"""
    res = client.get("/api/jokes")
    assert res.status_code == 200
    data = res.get_json()
    # 不断言 count == 14：因为投稿接口会往 jokes 里加数据（包括本文件自己的测试）。
    # 断"接口返回的数 == 内存列表长度"，无论数据怎么变都成立
    assert data["count"] == len(jokes)


def test_missing_joke_returns_404():
    """访问不存在的 /api/joke/999，应该返回 404"""
    res = client.get("/api/joke/999")
    # 这个测试防的是"回归"：万一哪天有人把 404 逻辑删了，它会立刻报警
    assert res.status_code == 404


def test_add_joke():
    """POST 投稿一条新笑话：返回 201，且总数 +1
    注意：这个测试会真的往 jokes 里加一条并写入 jokes.json（测试客户端直接操作数据）"""
    # before/after 对比：测"变化量"而不是"绝对值"——不受历史数据影响
    before = len(jokes)
    # json= 参数：client 自动帮你把字典转成 JSON 身体并设好 Content-Type——
    # 和 client.html 里手写三件套是同一件事，测试框架帮你打包了
    res = client.post("/api/joke", json={"setup": "测试铺垫", "punchline": "测试包袱"})
    assert res.status_code == 201
    assert len(jokes) == before + 1


def test_add_joke_rejects_empty():
    """POST 空内容：后端要挡住，返回 400"""
    # 测"坏输入被挡住"和测"好输入能通过"一样重要——安全边界要靠测试守住
    res = client.post("/api/joke", json={"setup": "", "punchline": ""})
    assert res.status_code == 400
