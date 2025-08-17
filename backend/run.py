# flake8: noqa: E402
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

PORT_BACK = int(os.getenv("PORT_BACK"))

if __name__ == "__main__":
    uvicorn.run(
        "modules.api.main:app", host="0.0.0.0", port=PORT_BACK, reload=True
    )