import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
import redis.asyncio as redis

redis_client: redis.Redis=None
lua_sha: str=None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ FastAPI lifespan manager
    Runs startup tasks before the app runs and cleanup tasks after the app shuts down
    """
    global redis_client, lua_sha

    redis_client=redis.Redis(
        host='localhost', port=6379, db=0, decode_responses=True
    )

    with open("ratelimit.lua", "r") as f:
        lua_script=f.read()

    lua_sha =await redis_client.script_load(lua_script)
    print(f"\n[SUCCESS] Lua script pre loaded into Redis memory! SHA:{lua_sha}\n")

    yield

    await redis_client.close()

app=FastAPI(title="Distributed Rate Limiter Gateway", lifespan=lifespan)

@app.get("/api/v1/resource")
async def limited_endpoint(request:Request, response:Response):
    """ Protected endpoint:
    Configured bucket capacity= 5 tokens
    Refill rate= 1 token per second
    """
    client_ip=request.client.host if request.client else "127.0.0.1"
    rate_key=f"rate_limit:{client_ip}"
    now=time.time()

    result=await redis_client.evalsha(lua_sha, 1, rate_key, 5, 1, now, 1)

    allowed=result[0]
    remaining_tokens=result[1]

    response.headers["X-Ratelimit-Remaining"]=str(remaining_tokens)

    if not allowed:
        response.status_code=status.HTTP_429_TOO_MANY_REQUESTS
        return {
            "error": "Too many requests",
            "message": "Rate limit exceeded, please try again later",
            "remaining tokens": remaining_tokens,
        }

    return {
        "status": "success",
        "message": "access granted!",
        "remaining_tokens": remaining_tokens,
    }