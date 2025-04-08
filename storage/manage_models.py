from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Lab3_models import Base
import yaml
import logging
import logging.config

# Load app configuration
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Load logging configuration
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Create logger
logger = logging.getLogger('basicLogger')

# Configure database connection
db_user = app_config['database']['user']
db_password = app_config['database']['password']
db_hostname = app_config['database']['hostname']
db_port = app_config['database']['port']
db_name = app_config['database']['db_name']

# Create database connection string
DATABASE_URL = f"mysql://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def create_tables():
    Base.metadata.create_all(engine)
    logger.info("Tables created successfully.")
    print("Tables created successfully.")

def drop_tables():
    Base.metadata.drop_all(engine)
    logger.info("Tables dropped successfully.")
    print("Tables dropped successfully.")

if __name__ == "__main__":
    while True:
        action = input("Choose an action: [create/drop/exit]: ").strip().lower()
        if action == "create":
            create_tables()
        elif action == "drop":
            drop_tables()
        elif action == "exit":
            logger.info("Exiting the script.")
            print("Exiting the script.")
            break
        else:
            print("Invalid option. Please choose 'create', 'drop', or 'exit'.")
