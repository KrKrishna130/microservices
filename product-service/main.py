from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import py_eureka_client.eureka_client as eureka_client

# The Gateway will use Eureka service discovery, and 
# async_do_service() provides client-side load balancing 
# when multiple instances are registered.
# ==================================================
# EUREKA STARTUP / SHUTDOWN
# ==================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    # ----------------------------
    # Startup
    # ----------------------------

    try:

        await asyncio.to_thread(
            eureka_client.init,
            eureka_server="http://localhost:8761/eureka",
            app_name="PRODUCT-SERVICE",
            instance_port=8004,
            instance_host="localhost"
        )

        print("PRODUCT-SERVICE registered with Eureka")

    except Exception as e:

        print(
            f"Failed to register PRODUCT-SERVICE "
            f"with Eureka: {e}"
        )

    yield

    # ----------------------------
    # Shutdown
    # ----------------------------

    try:

        eureka_client.stop()

        print("PRODUCT-SERVICE stopped")

    except Exception as e:

        print(
            f"Error stopping Eureka client: {e}"
        )


# ==================================================
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Product Service",
    lifespan=lifespan
)


# ==================================================
# RATE LIMITER
# ==================================================

limiter = Limiter(
    key_func=get_remote_address
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
async def health():

    return {
        "service": "product-service",
        "status": "UP"
    }


# ==================================================
# PRODUCT API
# ==================================================

@app.get("/products/{product_id}")
@limiter.limit("10/minute")
async def get_product(
    request: Request,
    product_id: int
):

    return {
        "product_id": product_id,
        "product_name": "Laptop",
        "price": 75000,
        "service": "PRODUCT-SERVICE"
    }


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004
    )