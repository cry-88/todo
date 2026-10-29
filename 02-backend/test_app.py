"""
笑话 API 的 pytest 测试
=======================

测试是"和代码逻辑对话"：你定好规则，让机器反复验证它。
运行方式（在 02-backend 目录下）：
    venv/Scripts/pytest -v

5 个测试：随机接口 / 总数 / 404 / POST 投稿成功 / POST 空内容被挡。
注意 test_joke_count 用 == len(jokes) 而不是写死数字——笑话库再增长，测试也不会失效。
"""
from app import app, jokes   # 能 import 成功，靠的就是 app.py 最后的 if __name__ == "__main__" 守卫

# pytest 需要一个"测试客户端"——不用真开服务器，直接调用接口
client = app.test_client()


def test_random_joke_ok():
    """随机接口应该返回 200，并且 body 里有 setup 和 punchline"""
    res = client.get("/api/joke/random")
    assert res.status_code == 200
    data = res.get_json()
    assert "setup" in data
    assert "punchline" in data


def test_joke_count():
    """总数接口应该返回 count=当前笑话数（用 len(jokes) 而不是写死数字，永不过期）"""
    res = client.get("/api/jokes")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] == len(jokes)


def test_missing_joke_returns_404():
    """访问不存在的 /api/joke/999，应该返回 404"""
    res = client.get("/api/joke/999")
    assert res.status_code == 404


def test_add_joke():
    """POST 投稿一条新笑话：返回 201，且总数 +1
    注意：这个测试会真的往 jokes 里加一条（测试客户端直接操作内存）"""
    before = len(jokes)
    res = client.post("/api/joke", json={"setup": "测试铺垫", "punchline": "测试包袱"})
    assert res.status_code == 201
    assert len(jokes) == before + 1


def test_add_joke_rejects_empty():
    """POST 空内容：后端要挡住，返回 400"""
    res = client.post("/api/joke", json={"setup": "", "punchline": ""})
    assert res.status_code == 400
