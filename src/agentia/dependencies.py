from fastapi import Request, WebSocket


def get_graph(request: Request = None, websocket: WebSocket = None):
    # 優先從 FastAPI 的注入對象獲取 app
    connection = request or websocket
    if connection:
        # 檢查 app.state 中是否有已初始化的 graph
        graph = getattr(connection.app.state, "graph", None)
        if graph:
            return graph
    
    # 相容性 Fallback：針對尚未改用 lifespan 的舊測試或手動呼叫
    from agentia import graph as graph_module
    fallback_graph = getattr(graph_module, "graph", None)
    
    if fallback_graph is None:
        raise RuntimeError("Graph not initialized")
    return fallback_graph


def get_db_pool(request: Request = None, websocket: WebSocket = None):
    connection = request or websocket
    if connection:
        pool = getattr(connection.app.state, "pool", None)
        if pool:
            return pool
    
    # 資料庫 Pool 沒有全域 Fallback（因為它是非同步初始化的）
    # 必須確保測試有使用 lifespan 或手動 override 此依賴
    raise RuntimeError("Database pool not initialized. Did you forget to use lifespan context?")


async def get_redis(request: Request = None, websocket: WebSocket = None):
    from agentia.memory import get_redis as _get_redis
    redis = await _get_redis()
    try:
        yield redis
    finally:
        await redis.aclose()
