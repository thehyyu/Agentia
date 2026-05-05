import pytest
from fastapi.testclient import TestClient
from agentia.main import app

def test_task_7_1_serve_index_html():
    """
    Task 7.1 TDD (RED): 驗證根目錄是否能正確提供 index.html。
    預期：目前 frontend 目錄不存在，應回傳 404。
    """
    client = TestClient(app)
    response = client.get("/")
    
    # 在 RED 階段，我們預期它是 404，因為目錄還沒建立，FastAPI 的 mount 條件不成立
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()
