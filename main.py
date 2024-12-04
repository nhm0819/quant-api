import logging.config
import uvicorn
import yaml
from fastapi.testclient import TestClient
from quant_api.apps.v1 import app

import directories

with open(directories.logging, "r") as stream:
    config = yaml.load(stream, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)


if __name__ == "__main__":
    # client = TestClient(app)
    # with client.websocket_connect("/ws_ping") as websocket:
    #     data = websocket.receive_json()
    #     print(data)

    uvicorn.run(
        "quant_api.apps.v1:app",
        host="127.0.0.1",
        port=8000,
        log_level="debug",
        reload=True,
    )
