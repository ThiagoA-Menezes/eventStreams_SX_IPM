# Kafka and StreamSets

![Banner](https://github.com/ThiagoA-Menezes/eventStreams_SX_IPM/blob/main/SX%20%2B%20Kafka.png?raw=true)
## Kafka, what is it?
Kafka is a distributed messaging system. The [Apache Kafka page](https://kafka.apache.org/intro) defines Kafka as a system equivalent to the human central nervous system and as the technological foundation for Always-on.  

Technically speaking, Kafka is simply the commonly known term for **Event Stream**, which is nothing more than the practice of capturing events at the moment they happen (**real-time**) from systems such as databases, sensors, mobile phones, cloud services, and other software that use this feature of sending events.  

In Kafka, these events are stored in **topics** for a defined period and, after that period expires, the information is deleted.  

Event Streaming can be used for many purposes, such as:  
- Monitoring a banking transaction to identify fraud  
- Mapping anomalous behavior in a sensor or system  
- Powering real-time data-driven applications  

---

## StreamSets, what is it used for?
StreamSets is a **cloud-native tool** used to build, run, and monitor **data pipelines**.  

A pipeline describes the flow of data from its source to its destinations and defines how the data will be processed along the way. These pipelines can connect to multiple types of systems, including **Data Lakes, Data Warehouses, and on-premises relational databases**.  

As the pipeline runs, it is possible to view real-time statistics and information about errors along the data flow.  

StreamSets is a **data transformation tool** that supports:  
- Kafka topics (Event Streaming)  
- Relational databases with **ETL/ELT** in bulk/batch  
- **Change Data Capture (CDC)**  

---

## EventStreams
Before starting with StreamSets and Kafka, we will need **3 IBM Cloud services** (free plan available in Dallas region):  

- **DB2**  
- **EventStreams**  
- **Cloud Object Storage (COS)**  

After creating an EventStreams instance:  
1. Create a **Service Credential**.  
2. Copy its JSON content and save it locally as:  

```bash
ibm_credentials.json
```
3. Keep track of the file path because it will be required by the Python script.  

---

## COS (Cloud Object Storage)
After provisioning COS:  

1. Create an instance for storing the data.  
2. Generate a **Service Credential**.  
3. From the JSON file generated, we will need:  

```bash
{
    "access_key_id": "XXXXXX",
    "secret_access_key": "YYYYYY"
}
```
4. Find the **Public Endpoint** for your bucket under **Configuration**. If it’s not visible, scroll down the page.  

---

## DB2 (Optional)
If you want to use DB2 as a storage target:  

- Save the DB2 credential info into a notepad.  
- You will configure DB2 later for enrichment with StreamSets.  

---

## Validating Java
Let’s check if **Java** is installed. If not, I recommend installing version **17**:

```bash
java -version
```

## Kafka Setup (Mac with Homebrew)

1. Install Kafka:

```bash
brew install kafka
```

2. Start Kafka:

```bash
brew services start kafka
```

3. Check if Kafka service is running:

```bash
brew services info –all
```

4. Create a Kafka topic:

```bash
kafka-topics --create --topic process_events --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

5. Consume messages from the topic:

```bash
kafka-console-consumer --bootstrap-server localhost:9092 --topic process_events 
```

---

## Kafka Setup (Manual with Apache Tarball)
If you are not using Homebrew, download and extract Kafka manually:

```bash
tar -xvf kafka-3.9.1-src.tgz
```

Start **Zookeeper**:

```bash
./zookeeper-server-start.sh ../config/zookeeper.properties
```
 
Start **Kafka Broker**:

```bash
./kafka-server-start.sh ../config/server.properties
```

Return to step 4 above to create the topic.  

---

## Running the Generator Script
After Kafka is running, place the following files in the same folder:  

- `ibm_credentials.json`  
- `log_generator.py`  
- Event log source file  

Run the generator script:
```bash
python3 log_genrator.py
```

If everything is correct, Kafka will start producing events.  

To validate event emission:

```bash
kafka-console-consumer --bootstrap-server localhost:9092 --topic process_events
```
---

## StreamSets

### Cloning the Environment
1. In your deployment, open the **kebab menu** (three dots).  
2. Click **Clone** and rename the deployment (example: add your initials).  
3. Choose the **engine version** (recommended: 6.2.1 or higher).  

### Adding Stage Libraries
1. On the deployment screen, go to **Edit > Configure Engine > Stage Libraries**.  
2. Add the required stage libraries (or select **All Stages**).  
3. Save and Start your deployment.  

---

## Creating the Kafka Connection

Configuration for Kafka connection:  
- **Type**: Kafka  
- **brokerURL**: list of brokers, comma-separated  
- **Security Option**: Custom Authentication (Protocol = Custom)  

Add the following **6 custom properties** from `bootstrap.ini` or EventStreams config:  
o	sasl.jaas.config
o	security.protocol
o	sasl.mechanism
o	ssl.protocol
o	ssl.enabled.protocols
o	ssl.endpoint.identification.algorithm


Click **TestConnection**.  

---

## Building the Pipeline

Add the following **stages**:  
- **Kafka Multitopic Consumer**  
- **Expression Evaluator**  
- **Field Order**  
- **Amazon S3**

### Configurations

**1. Kafka Multitopic Consumer**  
- Connection: Kafka connection created  
- Consumer Group: `streamsetsDataCollector`  
- Topic Subscription Type: `Topics List`
- Topic List: `process_events`  
- Data Format: `JSON`  

**2. Expression Evaluator**  
- Output Fields:  
- 	/"Case ID"
-	/Activity
-	/"Event Time"
-	/"Product ID"

- Field Expression: 
-	${record:value("/Case ID")}
-	${record:value('/Activity')}
-	${record:value("/Event Time")}
-	${record:value("/Product ID")}


**3. Field Order**  
Fields must include `/` prefix:  
-	/"Case ID" 
-	/Activity 
-	/"Event Time"
-	/"Product ID"


**4. Amazon S3**  
- Connection: select connection  
- Bucket: bucket name  
- Object Name Suffix: `CSV`  
- Data Format: Delimited (with header line)  

---

## Running the Pipeline
If Kafka has been producing data, when you run Draft Mode:  

- Draft Run > Reset Origin & Start

You will immediately see events being consumed and flowing through the pipeline.  

---

## DB2 Enrichment with JDBC Lookup (Optional)

Example configuration:  

**JDBC Connection String:**

```bash
jdbc:db2://<hostname>:<port>/BLUDB
```

**SQL Query Example:**
```bash
SELECT ID_PRODUCT, DESCRIPTION
FROM TZX44874.DB2_product_lookup
WHERE ID_PRODUCT = '${record:value("/Product ID")}'
```

**Properties:**
```bash
sslConnection=true
```

Download the DB2 JDBC driver from IBM (https://www.ibm.com/support/pages/db2-jdbc-driver-versions-and-downloads):  
- Extract `db2jcc4.jar`
- Upload it into **External Libraries** for the JDBC Lookup stage  

---

## Troubleshooting
If DB2 stage errors occur:  

1. Access the engine machine:
```bash
cd /home/<user>/sdc/streamsets-datacollector-6.2.1/etc
```

2. Open the properties file:
```bash
vi sdc.properties
```

3. Update the Flight Service setting:  
```bash
flight.enable = true
```
(Replace `auto` with `true`)  

4. Restart the engine.  

---

🎉 **Congratulations!** You just completed the **Kafka + StreamSets Lab** successfully!