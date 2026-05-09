import os
import logging
import uvicorn

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
