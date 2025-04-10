import connexion
from sqlalchemy import select
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Lab3_models import Base, DronePositionEvent, TargetAcquisitionEvent
from datetime import datetime
import yaml
import logging
import logging.config
import json
import os
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware


with open('/app/config/app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())


db_user = app_config['database']['user']
db_password = app_config['database']['password']
db_hostname = app_config['database']['hostname']
db_port = app_config['database']['port']
db_name = app_config['database']['db_name']
database_url = f"mysql://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"


with open('/app/log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
    logger = logging.getLogger('storage')

# Database setup
DB_ENGINE = create_engine(database_url)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

def process_messages():


    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    topic_name = app_config['events']['topic']

    logger.info(f"Connecting to Kafka at {hostname}, topic {topic_name}")

    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(topic_name)]


    consumer = topic.get_simple_consumer(
        consumer_group=b'event_group',
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST
    )

    logger.info("Consumer created and waiting for messages...")


    for msg in consumer:
        try:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            logger.info(f"Message received: {msg}")

            payload = msg["payload"]

            if msg["type"] == "drone_position":

                logger.info(f"Processing drone position event with trace_id: {payload['trace_id']}")
                store_drone_position(payload)

            elif msg["type"] == "target_acquisition":

                logger.info(f"Processing target acquisition event with trace_id: {payload['trace_id']}")
                store_target_acquisition(payload)
            consumer.commit_offsets()

        except Exception as e:
            logger.error(f"Error processing message: {e}")

def store_drone_position(payload):

    session = DB_SESSION()
    timestamp = datetime.strptime(payload['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")

    position = DronePositionEvent(
        drone_id=payload['drone_id'],
        latitude=payload['latitude'],
        longitude=payload['longitude'],
        altitude=payload['altitude'],
        signal_strength=payload['signal_strength'],
        timestamp=timestamp,
        trace_id=payload['trace_id']
    )

    session.add(position)
    session.commit()
    session.close()

    logger.debug(f"Stored event drone_position with a trace id of {payload['trace_id']}")

def store_target_acquisition(payload):

    session = DB_SESSION()
    timestamp = datetime.strptime(payload['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")

    acquisition = TargetAcquisitionEvent(
        drone_id=payload['drone_id'],
        target_id=payload['target_id'],
        acquisition_type=payload['acquisition_type'],
        target_type=payload['target_type'],
        latitude=payload['latitude'],
        longitude=payload['longitude'],
        altitude=payload['altitude'],
        certainty=payload['certainty'],
        timestamp=timestamp,
        trace_id=payload['trace_id']
    )

    session.add(acquisition)
    session.commit()
    session.close()

    logger.debug(f"Stored event target_acquisition with a trace id of {payload['trace_id']}")

def get_drone_positions(start_timestamp, end_timestamp):
    start_dt = datetime.fromisoformat(start_timestamp)
    end_dt = datetime.fromisoformat(end_timestamp)

    session = DB_SESSION()

    statement = select(DronePositionEvent).where(
        DronePositionEvent.timestamp >= start_dt,
        DronePositionEvent.timestamp < end_dt
    )

    results = [result.to_dict() for result in session.execute(statement).scalars().all()]

    logger.info("Found %d drone position events (start: %s, end: %s)", len(results), start_dt, end_dt)

    session.close()
    return results, 200

def get_target_acquisitions(start_timestamp, end_timestamp):
    start_dt = datetime.fromisoformat(start_timestamp)
    end_dt = datetime.fromisoformat(end_timestamp)

    session = DB_SESSION()

    statement = select(TargetAcquisitionEvent).where(
        TargetAcquisitionEvent.timestamp >= start_dt,
        TargetAcquisitionEvent.timestamp < end_dt
    )

    results = [result.to_dict() for result in session.execute(statement).scalars().all()]
    logger.debug(f"Start Timestamp: {start_dt}, End Timestamp: {end_dt}")

    logger.info("Found %d target acquisition events (start: %s, end: %s)", len(results), start_dt, end_dt)

    session.close()
    return results, 200

def setup_kafka_thread():

    logger.info("Setting up Kafka consumer thread")
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    logger.info("Kafka consumer thread setup complete")

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/storage", strict_validation=True, validate_responses=True)


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
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")
