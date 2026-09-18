import os

import oracledb
from dotenv import load_dotenv


load_dotenv()
_client_initialized = False


def _init_oracle_client():
    """Use Thick mode only when an Instant Client path is explicitly set."""
    global _client_initialized
    if _client_initialized:
        return

    client_dir = os.getenv("ORACLE_CLIENT_DIR")
    if client_dir:
        oracledb.init_oracle_client(lib_dir=client_dir)
    _client_initialized = True


def connect_db():
    """Create an Oracle connection from environment variables."""
    _init_oracle_client()

    return oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        host=os.getenv("ORACLE_HOST", "localhost"),
        port=int(os.getenv("ORACLE_PORT", "1521")),
        service_name=os.getenv("ORACLE_SERVICE", "XEPDB1"),
    )
