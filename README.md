# schema-registry-testing
The purpose of this repo is to test a number of different scenarios:

- Export all schemas from one registry and import into a new empty registry
- Export all schemas from one registry and import into another registry which already contains schemas
- Using the scripts with source schemas in contexts

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

# Scenario 1 - Export all schemas from one registry and import into a new empty registry
In this scenario, we will first populate Schema Registry 1 with some schemas. 
We will then export them all to a local directory and then import them into a Schema Registry 2 which will be empty
All the imported schemas will have the same ids and versions as the original schemas in Schema Registry 1

### Upload schemas to Schema Registry 1
From the root of this repository you can run
```
sh ./scripts/load-schemas.sh --all --folder schemas/scenario_1 --registry http://localhost:8081
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

### Export the schemas with Ids and versions from Schema Registry 1
From the root of this repository you can run
```
python scripts/export-schema-registry.py --url http://localhost:8081
```

The above command will create a folder named `export` and export all schemas to folders within it by subject name

### Import the schemas into Schema Registry 2
From the root of this repository  you can run
```
python scripts/import-schema-registry.py --url http://localhost:8082 --import-folder export
```

This will import the schemas into Schema Registry 2, maintaining the same version and id for each schema. The output will look similar to the below
```
- Processing Subjects
        Processing Subject subject3 with path export\default\subject3
                Attempting to put subject3 into IMPORT mode
                Subject: subject3 is now in IMPORT mode
                        - Processing file export\default\subject3\1.json
                        - Processing file export\default\subject3\2.json
                Subject: subject3 is now in READWRITE mode


        Processing Subject subject2 with path export\default\subject2
                Attempting to put subject2 into IMPORT mode
                Subject: subject2 is now in IMPORT mode
                        - Processing file export\default\subject2\1.json
                Subject: subject2 is now in READWRITE mode


        Processing Subject subject1 with path export\default\subject1
                Attempting to put subject1 into IMPORT mode
                Subject: subject1 is now in IMPORT mode
                        - Processing file export\default\subject1\1.json
                Subject: subject1 is now in READWRITE mode


Import Results:
{'subject3': {1: 'IMPORTED', 2: 'IMPORTED'}, 'subject2': {1: 'IMPORTED'}, 'subject1': {1: 'IMPORTED'}}
```

# Scenario 2 - Export all schemas from one registry and import into a new empty registry
**Before proceeding, please ensure both registries are cleared down**

This scenario is similar to Scenario 1 except that the target registry already contains schemas and we need to import with an import-context

### Upload schemas to Schema Registry 1 (Using schemas from scenario 1)
```
sh ./scripts/load-schemas.sh --all --folder schemas/scenario_1 --registry http://localhost:8081

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

### Upload 'existing' schems to Schema Registry 2
```
sh ./scripts/load-schemas.sh --all --folder schemas/scenario_2 --registry http://localhost:8082

Uploading schema for subject: subject4 from file schemas/scenario_2/subject4-v1.avsc
{"id":1}

Uploading schema for subject: subject5 from file schemas/scenario_2/subject5-v1.avsc
{"id":2}
```

From the outputs above, we can see that both registries have schemas with the same ids:
```
{"id":1}
{"id":2}
```
This means that when importing schemas from one registry to another there will be id conflicts with these specific schemas. We need to ensure the ids remain the same during migration to ensure data can continue to be correctly deserialised by consumer. But more importabtly, we do not want to overwrite or change existing schemas in the target registry in any way

Other conflicts around subject names can also occur and overall this means we need to be extemely careful when importing schemas into an already populated registry

The import script has a number of safety mechanisms in place to ensure that existing target schemas are not impacted by an import:

- If the target registry contains schemas, then you must provide a context to import the schemas into
- The context that is provided must not already exist

When you provide a context, the imported schemas are placed into their own 'namespace' and maintain their ids. This means that within a schema registry, there can be multiple schemas with the same id, however they will all exist within different contexts

### Export the schemas with ids and versions from Schema Registry 1
From the root of this repository you can run
```
python scripts/export-schema-registry.py --url http://localhost:8081
```

The above command will create a folder named `export` and export all schemas to folders within it by subject name

### Import the schemas into Schema Registry 2
If we run the same command to import as with Scenario 1 we will get an error message

```
python scripts/import-schema-registry.py --url http://localhost:8082 --import-folder export

The target schema registry contains subjects and no import context has been provided
In order to prevent any unintended overwrites, if subjects already exist in a target registry, you must provide an import context using --import-context
Please note that the import context you provide must not already exist in the target registry
This script will now exit
```

We need to provide a context with the `--import-context` flag. The context must not already exist in the target registry
```
python scripts/import-schema-registry.py --url http://localhost:8082 --import-folder export --import-context my-context

- Processing Subjects
        Processing Subject :.my-context:subject1 with path export\default\subject1
                Attempting to put :.my-context:subject1 into IMPORT mode
                Subject: :.my-context:subject1 is now in IMPORT mode
                        - Processing file export\default\subject1\1.json
                Subject: :.my-context:subject1 is now in READWRITE mode


        Processing Subject :.my-context:subject2 with path export\default\subject2
                Attempting to put :.my-context:subject2 into IMPORT mode
                Subject: :.my-context:subject2 is now in IMPORT mode
                        - Processing file export\default\subject2\1.json
                Subject: :.my-context:subject2 is now in READWRITE mode


        Processing Subject :.my-context:subject3 with path export\default\subject3
                Attempting to put :.my-context:subject3 into IMPORT mode
                Subject: :.my-context:subject3 is now in IMPORT mode
                        - Processing file export\default\subject3\1.json
                        - Processing file export\default\subject3\2.json
                Subject: :.my-context:subject3 is now in READWRITE mode


Import Results:
{':.my-context:subject1': {'1': 'IMPORTED'}, ':.my-context:subject2': {'1': 'IMPORTED'}, ':.my-context:subject3': {'1': 'IMPORTED', '2': 'IMPORTED'}}
```

You can see that the imported subjects are now within a context `my-context`.
```
 curl -s localhost:8082/subjects

[":.my-context:subject1",":.my-context:subject2",":.my-context:subject3","subject4","subject5
```

You can also confirm that the ids have been maintained, including the ones that would have caused a conflict. 
The following is one of the existing subjects with `{"id": 1}`
```
curl -s localhost:8082/subjects/subject4/versions/1

{"subject":"subject4","version":1,"id":1,"schema":"{\"type\":\"record\",\"name\":\"Schema1\",\"namespace\":\"example\",\"fields\":[{\"name\":\"schema1Name\",\"type\":\"string\"},{\"name\":\"schema1Age\",\"type\":\"int\"}]}"}
```

The following is one of the imported schemeas which also continues to have `{"id": 1}`. As this is within the `my-context` context, there is no conflict
```
curl -s localhost:8082/subjects/:.my-context:subject1/versions/1

{"subject":":.my-context:subject1","version":1,"id":1,"schema":"{\"type\":\"record\",\"name\":\"Schema1\",\"namespace\":\"example\",\"fields\":[{\"name\":\"schema1Name\",\"type\":\"string\"},{\"name\":\"schema1Age\",\"type\":\"int\"}]}"}
```

Please note that if you attempt to run this command again using the same value for `--import-context` then this will fail as shown below
```
python scripts/import-schema-registry.py --url http://localhost:8082 --import-folder export --import-context my-context

The import context you have provided: my-context already exists in the schema registry
In order to prevent any unintended overwrites, please provide a context that does not already exist
This script will now exit
```

You will need to provide a new import context that does not already exist for this to be successful

One you have imported your schemas into a new context, you need to change the client URL.
Instead of:
```
http://localhost:8082
```

We update the URL to consider the context
```
http://localhost/contexts/:.my-context'
```

This means that clients will access the `/subjects/<subject_name>` and will not know that the schema is part of a context
```
curl -s http://localhost:8082/contexts/:.my-context/subjects/subject1/versions/1

{"subject":":.my-context:subject1","version":1,"id":1,"schema":"{\"type\":\"record\",\"name\":\"Schema1\",\"namespace\":\"example\",\"fields\":[{\"name\":\"schema1Name\",\"type\":\"string\"},{\"name\":\"schema1Age\",\"type\":\"int\"}]}"}
```

# Scenario 3 - Using the scripts with source schemas in contexts
**Before proceeding, please ensure both registries are cleared down**

This is a slighty more advanced scenario where the source schema registry may contain schemas which are within contexts. 
Additionally it is possible the schemas may be part of a nested context structure. 
In both these scenarios, when the export happens, folders are created to represent the hierarchy. When importing, you still need to provide an import-context if the target registry contains schemas

### Upload schemas within contexts to Schema Registry 1

The below command adds a schema with the `my-context` context
```
cat schemas/scenario_1/subject1-v1.avsc | \
jq -c '. | { schema: . | @json }' | \
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data-binary @- "http://localhost:8081/subjects/:.my-context:subject1/versions" | jq

{
  "id": 1
}
```
The following adds another schema with the `my-context.sub-context` nested context
```
cat schemas/scenario_1/subject2-v1.avsc | \
jq -c '. | { schema: . | @json }' | \
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data-binary @- "http://localhost:8081/subjects/:.my-context.sub-context:subject2/versions" | jq

{
  "id": 1
}
```

We can export these as normal with the following command
```
python scripts/export-schema-registry.py http://localhost:8081
```

This will created the following file structure 
```
- export
    - contexts
        - my-context
            - subject1
                - 1.json
            - sub-context
                - subject2
                    - 1.json
```

When importing to an empty target schema, you do not need to provide a `--import-context`. The following will work as expected
```
python scripts/import-schema-registry.py --url http://localhost:8082 --import-folder export

- Processing Subjects
        Processing Subject :.my-context.sub-context:subject2 with path export\contexts\my-context\sub-context\subject2
                Attempting to put :.my-context.sub-context:subject2 into IMPORT mode
                Subject: :.my-context.sub-context:subject2 is now in IMPORT mode
                        - Processing file export\contexts\my-context\sub-context\subject2\1.json
                Subject: :.my-context.sub-context:subject2 is now in READWRITE mode


        Processing Subject :.my-context:subject1 with path export\contexts\my-context\subject1
                Attempting to put :.my-context:subject1 into IMPORT mode
                Subject: :.my-context:subject1 is now in IMPORT mode
                        - Processing file export\contexts\my-context\subject1\1.json
                Subject: :.my-context:subject1 is now in READWRITE mode


Import Results:
{':.my-context.sub-context:subject2': {'1': 'IMPORTED'}, ':.my-context:subject1': {'1': 'IMPORTED'}}
```

When importing to a target registry that already contains subjects, you must provide a `--import-context`. 
In this case the import context is prepended to any contexts that were exported

You can see in the below example that `new-import` was provided and is applied as expected
```
python scripts/import-schema-registry.py --url http://localhost:8082 --import-folder export --import-context new-import

- Processing Subjects
        Processing Subject :.new-import.my-context:subject1 with path export\contexts\my-context\subject1
                Attempting to put :.new-import.my-context:subject1 into IMPORT mode
                Subject: :.new-import.my-context:subject1 is now in IMPORT mode
                        - Processing file export\contexts\my-context\subject1\1.json
                Subject: :.new-import.my-context:subject1 is now in READWRITE mode


        Processing Subject :.new-import.my-context.sub-context:subject2 with path export\contexts\my-context\sub-context\subject2
                Attempting to put :.new-import.my-context.sub-context:subject2 into IMPORT mode
                Subject: :.new-import.my-context.sub-context:subject2 is now in IMPORT mode
                        - Processing file export\contexts\my-context\sub-context\subject2\1.json
                Subject: :.new-import.my-context.sub-context:subject2 is now in READWRITE mode


Import Results:
{':.new-import.my-context:subject1': {'1': 'IMPORTED'}, ':.new-import.my-context.sub-context:subject2': {'1': 'IMPORTED'}}
```

As the above exist in different subcontexts, you must change the URL of your clients

This is the new URL for accessing schemas in `my-context`
```
curl -s http://localhost:8082/contexts/:.new-import.my-context/subjects
[":.new-import.my-context:subject1"]
```

This is the new URL for accessing schemas in `my-context.sub-context`
```
curl -s http://localhost:8082/contexts/:.new-import.my-context.sub-context/subjects
[":.new-import.my-context.sub-context:subject2"]
```

## Useful Commands

### List Topics
```
docker run --rm --network=host confluentinc/cp-kafka:7.3.5 /usr/bin/kafka-topics --list --bootstrap-server localhost:9092
```

### Upload a single schema using Curl
```
cat schemas/scenario_1/subject1-v1.avsc | \
jq -c '. | { schema: . | @json }' | \
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" --data-binary @- http://localhost:8081/subjects/subject1/versions | jq
```

### Upload a single schemas using Curl with a context applied
In this instance, we are adding the schema to a context named "my-context"

```
cat schemas/scenario_1/subject2-v1.avsc | \
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

### Manually export a schema
```
curl -s localhost:8081/subjects/subject3/versions/1 > subject3_v1.json
```

### Manually import a schema into a new empty registry

First put the subject into IMPORT mode on the target registry
```
curl -s -X PUT -H "Content-Type": "application/vnd.schemaregistry.v1+json" "http://localhost:8082/mode/subject3" -d '{ "mode": "IMPORT" }'
```

Import the subject
```
cat subject3_v1.json | jq '.| del(.subject)' | curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" http://localhost:8082/subjects/subject3/versions --data-binary @-
```

Return the subject to READWRITE mode
```
curl -s -X PUT -H "Content-Type": "application/vnd.schemaregistry.v1+json" "http://localhost:8082/mode/subject3" -d '{ "mode": "READWRITE" }'
```

Verify the schema has the expected id
```
curl -s http://localhost:8082/subjects/subject3/versions/1 | jq '.id'
```