from fastapi import FastAPI, HTTPException

from services.razorpay_service import RazorpayService


app = FastAPI(
    title="RecoverAI",
    description="AI Revenue Recovery Agent for Razorpay",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "project": "RecoverAI",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/razorpay/test")
def razorpay_test():

    try:
        razorpay_service = RazorpayService()

        orders = razorpay_service.get_orders(count=5)

        return {
            "connected": True,
            "orders": orders
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )