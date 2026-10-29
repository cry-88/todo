"""
D2 拓展任务：给笑话 API 写测试
==============================

测试是"和代码逻辑对话"：你定好规则，让机器反复验证它。
运行方式（在 02-backend 目录下）：
    venv/Scripts/pytest -v

第 1 个测试是写好的例子。先读它，再把下面两个 TODO 补完，最后跑一遍看 3 个全绿。
"""

from app import app   # 能 import 成功，靠的就是 app.py 最后的 if __name__ == "__main__" 守卫

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
    """TODO 1: /api/jokes 应该返回 count=6，且 jokes 列表长度为 6
    提示：res.get_json() 拿到字典后，访问键值对和 Python 字典一样
    """
    ...


def test_missing_joke_returns_404():
    """TODO 2: 访问不存在的 /api/joke/999，应该返回 404
    提示：状态码用 res.status_code 判断，参考上面的例子
    """
    ...
