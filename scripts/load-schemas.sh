#!/bin/bash

# Initialize variables with default values
all=false
schema_file=""
registry_url=""
folder=""

# Function to upload a schema to the schema registry
upload_schema() {
  local subject="$1"
  local file="$2"
  
  printf "\n\nUploading schema for subject: $subject from file $file\n"
  
  # Use jq to compact and stringify the JSON content of the schema file
  payload=$(jq -c '. | { schema: . | @json }' < "$file")

  # Use curl to send the JSON payload to the schema registry
  curl -X POST -s -H "Content-Type: application/vnd.schemaregistry.v1+json" \
    --data "$payload" "$registry_url/subjects/$subject/versions"
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      all=true
      shift
      ;;
    --schema)
      if [[ -f "$2" ]]; then
        schema_file="$2"
        shift 2
      else
        echo "Invalid schema file specified."
        exit 1
      fi
      ;;
    --registry)
      registry_url="$2"
      shift 2
      ;;
    --folder)
      folder="$2"
      shift 2
      ;;
    *)
      echo "Invalid argument: $1"
      exit 1
      ;;
  esac
done

# Check if --registry is provided and not empty
if [ -z "$registry_url" ]; then
  echo "The --registry flag is mandatory. Please specify the schema registry URL."
  exit 1
fi

# If using --all, check if --folder is provided and not empty
if [ "$all" = true ]; then
  if [ -z "$folder" ]; then
    echo "The --folder flag is mandatory when using --all. Please specify the folder containing the schema files."
    exit 1
  fi
fi

# If neither --all nor --schema is provided, show usage and exit
if [[ ! "$all" && -z "$schema_file" ]]; then
  echo "Usage: $0 [--all --folder <folder>] | [--schema <schema_file>] --registry <registry_url>"
  exit 1
fi

# Process all schemas or a single schema
if [ "$all" = true ]; then
  for schema_file in $(ls -1 "$folder"/*.avsc | sort -t'-' -k1,1 -k3,3n); do
    subject=$(basename "$schema_file" | cut -d'-' -f1)
    upload_schema "$subject" "$schema_file"
  done
else
  subject=$(echo "$schema_file" | cut -d'-' -f1)
  upload_schema "$subject" "$schema_file"
fi
