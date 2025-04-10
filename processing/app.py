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
app.add_api("openapi.yml", base_path="/processing", strict_validation=True, validate_responses=True)


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
    create_files_if_not_exist()
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
