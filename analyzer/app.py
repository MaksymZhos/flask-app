import connexion
import yaml
import logging
import logging.config
import json
import os
from pykafka import KafkaClient
from pykafka.common import OffsetType
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime

with open('/app/config/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('/app/log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('analyzer')

def get_drone_position(index):


    logger.info(f"Request for drone position at index {index}")

    # Connect to Kafka
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True,
        consumer_timeout_ms=1000
    )


    drone_position_index = 0
    logger.info(f"Searching for drone position at index {index}")

    for msg in consumer:
        if msg:
            message = msg.value.decode('utf-8')
            msg_data = json.loads(message)


            if msg_data.get('type') == 'drone_position':
                if drone_position_index == int(index):
                    logger.info(f"Found drone position at index {index}")
                    return msg_data['payload'], 200
                drone_position_index += 1

    logger.error(f"No drone position message found at index {index}")
    return {"message": f"No drone position message found at index {index}"}, 404

def get_target_acquisition(index):


    logger.info(f"Request for target acquisition at index {index}")


    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True,
        consumer_timeout_ms=1000
    )


    target_acquisition_index = 0
    logger.info(f"Searching for target acquisition at index {index}")

    for msg in consumer:
        if msg:
            message = msg.value.decode('utf-8')
            msg_data = json.loads(message)


            if msg_data.get('type') == 'target_acquisition':
                if target_acquisition_index == int(index):
                    logger.info(f"Found target acquisition at index {index}")
                    return msg_data['payload'], 200
                target_acquisition_index += 1

    logger.error(f"No target acquisition message found at index {index}")
    return {"message": f"No target acquisition message found at index {index}"}, 404

def get_stats():


    logger.info("Request for event stats")


    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True,
        consumer_timeout_ms=1000
    )


    drone_position_count = 0
    target_acquisition_count = 0

    for msg in consumer:
        if msg:
            message = msg.value.decode('utf-8')
            msg_data = json.loads(message)

            if msg_data.get('type') == 'drone_position':
                drone_position_count += 1
            elif msg_data.get('type') == 'target_acquisition':
                target_acquisition_count += 1

    stats = {
        'num_drone_position': drone_position_count,
        'num_target_acquisition': target_acquisition_count
    }

    logger.info(f"Event stats: {stats}")
    return stats, 200

def health():

    return {"status": "running"}, 200

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/analyzer", strict_validation=True, validate_responses=True)


if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


if __name__ == "__main__":
    app.run(port=8200, host="0.0.0.0")
