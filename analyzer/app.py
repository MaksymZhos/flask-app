import connexion
import yaml
import logging
import logging.config
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
from flask_cors import CORS
from datetime import datetime
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

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

    # Connect to Kafka
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
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)
CORS(app.app)

import connexion
import yaml
import json
import os
import logging
import logging.config
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

with open('/app/config/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Replace the basicConfig with proper config loading
with open('/app/log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('processing')
def get_stats():

    logger.info("Received request for statistics.")

    stats_file = app_config['datastore']['filename']

    if not os.path.isfile(stats_file):
        logger.error("Statistics file does not exist.")
        return {"message": "Statistics do not exist"}, 404

    with open(stats_file, 'r') as f:
        stats = json.load(f)

    logger.debug(f"Statistics data: {stats}")
    logger.info("Successfully retrieved statistics.")

    return stats, 200

def create_files_if_not_exist():
    if not os.path.isfile(app_config['datastore']['filename']):
        stats = {
            "num_drone_positions": 0,
            "num_target_acquisitions": 0,
            "max_signal_strength": 0,
            "max_certainty": 0,
            "last_updated": "2000-01-01T00:00:00.000000Z"
        }
        with open(app_config['datastore']['filename'], 'w') as f:
            json.dump(stats, f)

def populate_stats():
    with open(app_config['datastore']['filename'], 'r') as f:
        stats = json.load(f)


    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def fetch_and_update_events(url, event_type, timestamp_key, value_key):
        response = requests.get(url, params={
            'start_timestamp': stats['last_updated'],
            'end_timestamp': current_timestamp
        })
        if response.status_code == 200:
            events = response.json()
            stats[event_type] += len(events)
            for event in events:
                stats[value_key] = max(stats[value_key], event[timestamp_key])

    fetch_and_update_events(app_config['eventstores']['drone_positions']['url'], 'num_drone_positions', 'signal_strength', 'max_signal_strength')
    fetch_and_update_events(app_config['eventstores']['target_acquisitions']['url'], 'num_target_acquisitions', 'certainty', 'max_certainty')


    stats['last_updated'] = current_timestamp

    with open(app_config['datastore']['filename'], 'w') as f:
        json.dump(stats, f)

def init_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        populate_stats,
        'interval',
        seconds=app_config['scheduler']['interval']
    )
    scheduler.start()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

app = FlaskApp(__name__)
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
