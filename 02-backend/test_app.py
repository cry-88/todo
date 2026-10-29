"""
笑话 API 的 pytest 测试
=======================

测试是"和代码逻辑对话"：你定好规则，让机器反复验证它。
运行方式（在 02-backend 目录下）：
    venv/Scripts/pytest -v

3 个测试：第 1 个是例子，后两个按原 TODO 说明补完。
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
