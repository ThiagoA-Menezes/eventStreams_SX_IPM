######################################################################################################
# This is a script to generate a log file and send it to a Kafka topic.
# Author: Thiago Nicino Menezes
# Date: 2025-08-01
# São Paulo, Brazil
# This script is part of a process mining simulation.
######################################################################################################

# Let start by importing the necessary libraries
import csv
import json
import random
import time
from kafka import KafkaProducer
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os



# This script generates a log file and sends it to a Kafka topic.
# It is used to simulate a process mining scenario.
# It reads a CSV file with event data and sends each row as a JSON object to the Kafka topic.

kafka_broker = 'localhost:9092'
kafka_topic = 'process_events'
base_log_file = './base_event_log.csv'
credentials_json = './ibm_credentials.json' # <-- This credentials file is exported from IBM Cloud, when creating the APIKey, change the path if needed

# first we load the credentials file from IBMCloud.
with open(credentials_json, 'r') as file:
    credentials_cloud = json.load(file)
    brokers_list = credentials_cloud['bootstrap_endpoints']
    brokers = [broker.strip() for broker in brokers_list.split(',') if broker.strip()]
    username = credentials_cloud['user']
    password = credentials_cloud['password']

# I'll print to check if the file is reading correctly:
#print(brokers , " \n username: " + username,  " \n password: " +  password)

# Here we create the Kafka producer, using the credentials from the IBM Cloud
# and the brokers list.
# The value_serializer is used to convert the data to JSON format before sending it to the Kafka topic.
# If you want to test it locally, you can uncomment the first line and comment the second one.
producer = KafkaProducer(#bootstrap_servers=kafka_broker,
                         bootstrap_servers=brokers,
                         # Here I'll use the security protocol and the SASL mechanism to connect to the Kafka topic
                         security_protocol='SASL_SSL',
                         sasl_mechanism='PLAIN',
                         sasl_plain_username=username,
                         sasl_plain_password=password,                       
                         value_serializer=lambda v: json.dumps(v).encode('utf-8')
                         )

# Now we define the activities and products that will be used in the log file, also, we want to create a fake product list, could be anything, but for this example, I'll use a list of integers.
activities = ['Start Process', 'Activity A', 'Activity B', 'Activity C', 'Activity D', 'End Process']
product_list = [1, 2, 3, 4, 5]

# This function will load the base log file, if it exists, and return a list of dictionaries with the data.
def load_baselog(file_path):
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            return list(reader)
    except FileNotFoundError:
        return [
            print("Base log file not found. Starting with an empty log.")
        ]
                        
# Now, we want to create a new case, this function will return a dictionary with the case ID.
case_id_counter = 1  # This will be used to generate unique case IDs
def new_case(case_id_counter, current_date):
    return {
        # This 10d after the case_id_counter is to ensure that the case ID is always 10 digits long, with leading zeros if necessary.
        'Case_ID': f'20250801_{case_id_counter:03d}',
        "current_activity":0,
        "current_date":current_date,
        "Product_ID":random.choice(product_list),
        'Product_Description': f"Product {random.choice(product_list)}"
    }


# Now the main function will be responsible for generating the log file and sending it to the Kafka topic.
def main():
    base_log = load_baselog(base_log_file)
    case_id_counter = len(set([row['Case_ID'] for row in base_log])) + 1
    current_date = datetime.strptime(base_log[0]['Date'], '%Y-%m-%d').date() if base_log else datetime.now().date()

    cases = [new_case(case_id_counter, current_date)]
    case_id_counter += 1

    print(f"Starting the event generation for kafka topic: {kafka_topic}")

    # Since we need it to behave like a stream, we will use a while loop to generate the events.
    while True:
        current_case = cases[0]
        activity_index = current_case['current_activity']
        activity = activities[activity_index]
        event_time = f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        
        event = {
            'Case_ID': current_case['Case_ID'],
            'Activity': activity,
            'Event_Time': f"{current_case['current_date'].strftime('%Y-%m-%d')} {event_time}",
            'Product_ID': current_case['Product_ID'],
            'Product_Description': f"Product {current_case['Product_ID']}"
        }

        # Here is where we send the event to the Kafka topic.
        producer.send(kafka_topic, value=event)
        print(f"Sent: {event}")

        # Advance the activity or start a new case if all activities are done
        current_case['current_activity'] += 1
        if current_case['current_activity'] >= len(activities):
            cases[0] = new_case(case_id_counter, current_case['current_date'])
            case_id_counter += 1

        time.sleep(random.uniform(1, 5))


if __name__ == "__main__":
    main()

#producer.send(kafka_topic, value={'message': 'Hello, Kafka!'})
#producer.flush()
print(f"Message sent to Kafka topic {kafka_topic}")
# %%
