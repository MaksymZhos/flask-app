import connexion
from connexion import NoContent
import httpx
from datetime import datetime
import uuid
import yaml
import logging
import logging.config
import json
from pykafka import KafkaClient  # Add pykafka import

# Load configuration
with open('/app/config/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Load logging configuration
with open('/app/log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Create logger
logger = logging.getLogger('receiver')

# Configure Kafka client
client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
topic = client.topics[str.encode(app_config['events']['topic'])]

def log_drone_position(body):
    # If trace_id is not provided in the request, generate one
    if 'trace_id' not in body:
        body['trace_id'] = str(uuid.uuid4())

    trace_id = body.get('trace_id')

    # Log the received event
    logger.info(f"Received event drone_position with a trace id of {trace_id}")

    # Prepare the data
    data = {
        "drone_id": body.get('drone_id'),
        "latitude": body.get('latitude'),
        "longitude": body.get('longitude'),
        "altitude": body.get('altitude'),
        "signal_strength": body.get('signal_strength'),
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "trace_id": trace_id
    }

    # Create Kafka message
    producer = topic.get_sync_producer()
    msg = {
        "type": "drone_position",
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": data
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    # Log the message production
    logger.info(f"Produced drone_position event to Kafka with trace id {trace_id}")

    # Return fixed 201 status code
    return NoContent, 201

def log_target_acquisition(body):
    # If trace_id is not provided in the request, generate one
    if 'trace_id' not in body:
        body['trace_id'] = str(uuid.uuid4())

    trace_id = body.get('trace_id')

    # Log the received event
    logger.info(f"Received event target_acquisition with a trace id of {trace_id}")

    # Prepare the data
    data = {
        "drone_id": body.get('drone_id'),
        "target_id": body.get('target_id'),
        "acquisition_type": body.get('acquisition_type'),
        "target_type": body.get('target_type'),
        "latitude": body.get('latitude'),
        "longitude": body.get('longitude'),
        "altitude": body.get('altitude'),
        "certainty": body.get('certainty'),
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "trace_id": trace_id
    }

    # Create Kafka message
    producer = topic.get_sync_producer()
    msg = {
        "type": "target_acquisition",
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": data
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    # Log the message production
    logger.info(f"Produced target_acquisition event to Kafka with trace id {trace_id}")

    # Return fixed 201 status code
    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
