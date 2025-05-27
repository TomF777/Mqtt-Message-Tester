import logging
import os
from dotenv import load_dotenv


LOG_FORMAT = "%(levelname)s %(asctime)s \
    Function: %(funcName)s \
    Line: %(lineno)d \
    Message: %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
LOGGER = logging.getLogger(__name__)

# Load environment variables from the .env file
load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_BROKER_USER = os.getenv("MQTT_USERNAME")
MQTT_BROKER_PASSWORD = os.getenv("MQTT_PASSWORD")
TEST_TRACE = os.getenv("TEST_TRACE")