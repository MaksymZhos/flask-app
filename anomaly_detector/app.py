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

logger = logging.getLogger('anomaly_detector')

def update_anomalies():
    """
    Update anomalies by reading from Kafka queue and storing anomaly data in JSON file.
    Returns the number of anomalies detected.
    """
    logger.info("Starting anomaly detection update")

    # Connect to Kafka
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True,
        consumer_timeout_ms=1000
    )

    # Initialize anomaly storage
    anomalies = []
    anomaly_count = 0

    # Process messages from Kafka
    for msg in consumer:
        if msg:
            message = msg.value.decode('utf-8')
            msg_data = json.loads(message)

            # Check if the event contains an anomaly based on event type
            is_anomaly = False

            if msg_data.get('type') == 'drone_position':
                if msg_data.get('payload', {}).get('signal_strength', 100) < 60:
                    is_anomaly = True
            elif msg_data.get('type') == 'target_acquisition':
                if msg_data.get('payload', {}).get('certainty', 100) < 70:
                    is_anomaly = True

            if is_anomaly:
                # Mark the event as an anomaly
                msg_data['anomaly'] = True
                anomalies.append(msg_data)
                anomaly_count += 1

    # Write anomalies to JSON datastore
    with open(app_config['datastore']['filename'], 'w') as f:
        json.dump(anomalies, f, indent=4)

    logger.info(f"Anomaly detection complete. Found {anomaly_count} anomalies.")

    # Return count of anomalies detected
    return {"num_anomalies": anomaly_count}, 200

def get_anomalies(event_type=None):
    logger.info(f"Request to get anomalies with event_type filter: {event_type}")

    if not os.path.exists(app_config['datastore']['filename']):
        logger.error("Anomaly datastore file not found")
        return {"message": "Anomaly datastore not found"}, 404

    try:
        with open(app_config['datastore']['filename'], 'r') as f:
            anomalies = json.load(f)

        valid_event_types = ['drone_position', 'target_acquisition']
        if event_type and event_type not in valid_event_types:
            logger.error(f"Invalid event type provided: {event_type}")
            return {"message": f"Invalid event type. Must be one of: {', '.join(valid_event_types)}"}, 400

        if event_type:
            filtered_anomalies = [anomaly for anomaly in anomalies if anomaly.get('type') == event_type]
        else:
            filtered_anomalies = anomalies

        if not filtered_anomalies:
            logger.info("No anomalies found matching criteria")
            return None, 204
            
        # Transform anomalies to match the expected response schema
        transformed_anomalies = []
        for anomaly in filtered_anomalies:
            # Map the stored anomaly to the expected response format
            transformed = {
                "drone_id": anomaly.get('payload', {}).get('drone_id', 'unknown'),
                "event_id": anomaly.get('payload', {}).get('trace_id', 'unknown'),
                "trace_id": anomaly.get('payload', {}).get('trace_id', 'unknown'),
                "event_type": anomaly.get('type', 'unknown')
            }
            
            # Add anomaly-specific fields based on the event type
            if anomaly.get('type') == 'drone_position':
                signal_strength = anomaly.get('payload', {}).get('signal_strength', 0)
                transformed["anomaly_type"] = "Low Signal Strength"
                transformed["description"] = f"Detected: {signal_strength}; too low (threshold 60)"
            elif anomaly.get('type') == 'target_acquisition':
                certainty = anomaly.get('payload', {}).get('certainty', 0)
                transformed["anomaly_type"] = "Low Certainty"
                transformed["description"] = f"Detected: {certainty}; too low (threshold 70)"
            
            transformed_anomalies.append(transformed)

        logger.info(f"Returning {len(transformed_anomalies)} anomalies")
        return transformed_anomalies, 200

    except json.JSONDecodeError:
        logger.error("Invalid JSON data in anomaly datastore")
        return {"message": "Invalid data in anomaly datastore"}, 404
    except Exception as e:
        logger.error(f"Error retrieving anomalies: {str(e)}")
        return {"message": f"Error retrieving anomalies: {str(e)}"}, 500

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("anomaly.yaml", base_path="/anomaly_detector", strict_validation=True, validate_responses=True)


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
    app.run(port=8400, host="0.0.0.0")
