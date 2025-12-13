from fastapi import FastAPI


app = FastAPI(title="Dental Bot API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
