from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request, HTTPException

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import py_eureka_client.eureka_client as eureka_client

# ===========Micro services Communication================#

# Using Eureka Service Discovery, one service calls another by its registered service name.
# Use Eureka Service Discovery to find the target service.
# Call it using its service name, not hardcoded IP.
# Example: async_do_service("USER-SERVICE", "/users/1")


# ==============LoadBalancing======================#
# Eureka registers multiple instances of the same service.
# Client selects an available instance using service discovery.
# This provides client-side load balancing across instances.
# i.e:-
# response = await eureka_client.async_do_service(
#     "USER-SERVICE", "/users/1", method="GET", return_type="json"
# )

# Eureka automatically selects an available USER-SERVICE instance.
# Multiple instances can run on different ports for load balancing.


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
            app_name="API-GATEWAY",
            instance_port=8080,
            instance_host="localhost"
        )

        print("API-GATEWAY registered with Eureka")

    except Exception as e:

        print(
            f"Failed to register API-GATEWAY "
            f"with Eureka: {e}"
        )

    yield

    # ----------------------------
    # Shutdown
    # ----------------------------

    try:

        eureka_client.stop()

        print("API-GATEWAY stopped")

    except Exception as e:

        print(
            f"Error stopping Eureka client: {e}"
        )


# ==================================================
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="API Gateway",
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
        "service": "api-gateway",
        "status": "UP"
    }


# ==================================================
# USER SERVICE
# ==================================================

@app.get("/api/users/{user_id}")
@limiter.limit("20/minute")
async def get_user(
    request: Request,
    user_id: int
):

    try:

        response = await eureka_client.async_do_service(
            "USER-SERVICE",
            f"/users/{user_id}",
            method="GET",
            return_type="json"
        )

        return response

    except Exception as e:

        print(
            f"USER-SERVICE failed: {e}"
        )

        raise HTTPException(
            status_code=503,
            detail="User service unavailable"
        )


# ==================================================
# PRODUCT SERVICE
# ==================================================

@app.get("/api/products/{product_id}")
@limiter.limit("20/minute")
async def get_product(
    request: Request,
    product_id: int
):

    try:
# here Micro services LoadBalancing are used for product service
        response = await eureka_client.async_do_service(
            "PRODUCT-SERVICE",
            f"/products/{product_id}",
            method="GET",
            return_type="json"
        )

        return response

    except Exception as e:

        print(
            f"PRODUCT-SERVICE failed: {e}"
        )

        raise HTTPException(
            status_code=503,
            detail="Product service unavailable"
        )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080
    )