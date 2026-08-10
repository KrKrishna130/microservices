from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import py_eureka_client.eureka_client as eureka_client
# service registry done for Payments service
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
            app_name="PAYMENT-SERVICE",
            instance_port=8003,
            instance_host="localhost"
        )

        print("PAYMENT-SERVICE registered with Eureka")

    except Exception as e:

        print(
            f"Failed to register PAYMENT-SERVICE "
            f"with Eureka: {e}"
        )

    yield

    # ----------------------------
    # Shutdown
    # ----------------------------

    try:

        eureka_client.stop()

        print("PAYMENT-SERVICE stopped")

    except Exception as e:

        print(
            f"Error stopping Eureka client: {e}"
        )


# ==================================================
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Payment Service",
    lifespan=lifespan
)

# rate limiter added
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
        "service": "payment-service",
        "status": "UP"
    }


# ==================================================
# PAYMENT FUNCTION
# ==================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(
        multiplier=1,
        min=1,
        max=5
    ),
    retry=retry_if_exception_type(Exception)
)
async def process_payment(amount: float):

    print("Processing payment...")

    # Simulate payment processing

    if amount <= 0:

        raise ValueError(
            "Invalid payment amount"
        )

    return {
        "payment_status": "SUCCESS",
        "amount": amount
    }

# expetion handling
# ==================================================
# FALLBACK
# ==================================================

def payment_fallback(amount: float):

    return {
        "payment_status": "PENDING",
        "amount": amount,
        "message": "Payment service temporarily unavailable"
    }


# ==================================================
# PAYMENT API
# ==================================================

@app.post("/payments")
@limiter.limit("5/minute")
async def make_payment(
    request: Request,
    amount: float
):

    try:

        result = await process_payment(amount)

        return result

    except Exception as exception:

        print(
            f"Payment failed: {exception}"
        )

        return payment_fallback(amount)


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003
    )