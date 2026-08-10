from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import py_eureka_client.eureka_client as eureka_client

import httpx

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


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
            app_name="ORDER-SERVICE",
            instance_port=8002,
            instance_host="localhost"
        )

        print("ORDER-SERVICE registered with Eureka")

    except Exception as e:

        print(
            f"Failed to register ORDER-SERVICE "
            f"with Eureka: {e}"
        )

    yield

    # ----------------------------
    # Shutdown
    # ----------------------------

    try:

        eureka_client.stop()

        print("ORDER-SERVICE stopped")

    except Exception as e:

        print(
            f"Error stopping Eureka client: {e}"
        )


# ==================================================
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Order Service",
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
        "service": "order-service",
        "status": "UP"
    }


# ==================================================
# CALL USER SERVICE
# ==================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(
        multiplier=1,
        min=1,
        max=5
    ),
    retry=retry_if_exception_type(
        (
            httpx.RequestError,
            httpx.HTTPStatusError
        )
    )
)
async def call_user_service(user_id: int):

    response = await eureka_client.async_do_service(
        "USER-SERVICE",
        f"/users/{user_id}",
        return_type="json"
    )

    return response


# ==================================================
# USER FALLBACK
# ==================================================

def user_fallback(user_id: int):

    return {
        "user_id": user_id,
        "name": "Unknown User",
        "status": "FALLBACK"
    }


# ==================================================
# CALL PAYMENT SERVICE
# ==================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(
        multiplier=1,
        min=1,
        max=5
    ),
    retry=retry_if_exception_type(
        (
            httpx.RequestError,
            httpx.HTTPStatusError
        )
    )
)
async def call_payment_service(amount: float):

    response = await eureka_client.async_do_service(
        "PAYMENT-SERVICE",
        f"/payments?amount={amount}",
        method="POST",
        return_type="json"
    )

    return response


# ==================================================
# PAYMENT FALLBACK
# ==================================================

def payment_fallback(amount: float):

    return {
        "payment_status": "PENDING",
        "amount": amount,
        "message": "Payment temporarily unavailable"
    }


# ==================================================
# CREATE ORDER
# ==================================================

@app.post("/orders")
@limiter.limit("10/minute")
async def create_order(
    request: Request,
    user_id: int,
    amount: float
):

    # ----------------------------------------------
    # USER SERVICE
    # ----------------------------------------------

    try:

        user = await call_user_service(
            user_id
        )

    except Exception as exception:

        print(
            f"User service failed: {exception}"
        )

        user = user_fallback(
            user_id
        )


    # ----------------------------------------------
    # PAYMENT SERVICE
    # ----------------------------------------------

    try:

        payment = await call_payment_service(
            amount
        )

    except Exception as exception:

        print(
            f"Payment service failed: {exception}"
        )

        payment = payment_fallback(
            amount
        )


    # ----------------------------------------------
    # ORDER RESPONSE
    # ----------------------------------------------

    return {
        "order_status": "CREATED",
        "user": user,
        "payment": payment
    }


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002
    )