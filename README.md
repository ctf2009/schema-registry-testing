# schema-registry-testing


The purpose of this repo is to test a number of different scenarios:

- Manually exporting all schemas from the registry
- Manually importing all schemas to a new registry maintaining version and Id information 
- Manually importing all schemas to a new registry under a new context
- Schema linking example

The Docker Compose file included in the repository will start the following:

- Zookeeper
- Kafka
- Schema Registry 1 (Port 8081)
- Schema Registry 2 (Port 8082)

The Schema Registries are configured to push their data to different Kafka topics

# Prerequisites

You will need the following available

- JQ
- Python 3 (with the requests module installed via Pip)

# Scenario 1 - Manually Export all Subjects

In this scenario, we will first populate Schema Registry 1 with some schemas. We will then export them all to a local directory

### Upload schemas to Schema Registry 1

From the root of this repository you can run

```
sh ./scripts/load-schemas.sh --all --folder schemas --registry http://localhost:8081
```

You should get some output similar to the below

```
Uploading schema for subject: subject1 from file schemas/subject1-v1.avsc
{"id":1}

Uploading schema for subject: subject2 from file schemas/subject2-v2.avsc
{"id":2}

Uploading schema for subject: subject3 from file schemas/subject3-v1.avsc
{"id":3}

# Same Subject as the previous but a new version with a new field
Uploading schema for subject: subject3 from file schemas/subject3-v2.avsc
{"id":4}

```

### Export the schemas with Ids and versions

From the root of this repository you can run

```
python scripts/export-schema-registry.py http://localhost:8081
```

The above command will create a folder named `export` and export all schemas to folders within it by subject name

We will use this output to faciliate scenario 2


# Scenario 2 - Manually importing all schemas to a different registry maintaining version and Id information

This scenario involves importing all the exported schemeas from the previous scenario

In order to do this there are some initial steps that need to be performed


## Useful Commands

### List Topics
```
docker run --rm --network=host confluentinc/cp-kafka:7.3.5 /usr/bin/kafka-topics --list --bootstrap-server localhost:9092
```

### Upload a single schema using Curl
```
cat schemas/subject1-v1.avsc | \
jq -c '. | { schema: . | @json }' | \
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data-binary @- http://localhost:8081/subjects/subject1/versions | jq
```

### Upload a single schemas using Curl with a context applied
In this instance, we are adding the schema to a context names "my-context"

```
cat schemas/subject2-v1.avsc | \
jq -c '. | { schema: . | @json }' | \
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data-binary @- "http://localhost:8081/subjects/:.my-context:subject2/versions" | jq
```

### Verify that the context was created

```
curl -s http://localhost:8081/contexts | jq
[
  ".",
  ".my-context"
]
```

### List all subjects in a context

```
curl -s http://localhost:8081/subjects?subjectPrefix=":.my-context:" | jq
[
  ":.my-context:subject2"
]
```

### List all subjects

```
curl -s http://localhost:8081/subjects?subjectPrefix=":*:" | jq
[
  ":.my-context:subject2",
  "subject1",
  "subject2",
  "subject3"
]
```