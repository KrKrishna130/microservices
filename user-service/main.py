from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import py_eureka_client.eureka_client as eureka_client

# service registry for user -service
# -------------------------------------------------
# Eureka Startup / Shutdown
# -------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup
    try:
        await asyncio.to_thread(
            eureka_client.init,
            eureka_server="http://localhost:8761/eureka",
            app_name="USER-SERVICE",
            instance_port=8001,
            instance_host="localhost"
        )

        print("USER-SERVICE registered with Eureka")

    except Exception as e:
        print(f"Failed to register USER-SERVICE with Eureka: {e}")

    yield

    # Shutdown
    try:
        eureka_client.stop()
        print("USER-SERVICE stopped")

    except Exception as e:
        print(f"Error stopping Eureka client: {e}")


# -------------------------------------------------
# FastAPI Application
# -------------------------------------------------

app = FastAPI(
    title="User Service",
    lifespan=lifespan
)
# rate limiter added

# -------------------------------------------------
# Rate Limiter
# -------------------------------------------------

limiter = Limiter(
    key_func=get_remote_address
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# -------------------------------------------------
# Health Check added
# -------------------------------------------------

@app.get("/health")
async def health():
    return {
        "service": "user-service",
        "status": "UP"
    }


# -------------------------------------------------
# Get User
# -------------------------------------------------

@app.get("/users/{user_id}")
@limiter.limit("5/minute")
async def get_user(
    request: Request,
    user_id: int
):
    return {
        "user_id": user_id,
        "name": "Krishna Kumar",
        "email": "krishna@example.com"
    }


# -------------------------------------------------
# Create User
# -------------------------------------------------

@app.post("/users")
@limiter.limit("10/minute")
async def create_user(
    request: Request
):
    return {
        "message": "User created successfully"
    }


# -------------------------------------------------
# Run Application
# -------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001
    )