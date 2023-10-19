import requests
import sys
import os
import json
import re
import argparse

def read_schema_from_file(file_path):
    with open(file_path, 'r') as file:
        schema = json.load(file)
        if "subject" in schema:
            del schema["subject"]
        return schema

def put_subject_into_mode(url, username, password, subject, mode, indent = ""):
    mode_url = f"{url}/mode/{subject}"
    data = {
        "mode": mode
    }
    response = requests.put(mode_url, auth=(username, password), headers={"Content-Type": "application/vnd.schemaregistry.v1+json"}, json=data)
    if response.status_code == 200:
        print(f"{indent}Subject: {subject} is now in {mode} mode")
        return True
    else: 
        print(f"{indent}Unable to put Subject: {subject} into mode {mode}")
        return False

def send_schema_to_registry(url, username, password, subject, payload_data):   
    subject_url = f"{url}/subjects/{subject}/versions"
    response = requests.post(subject_url, auth=(username, password), headers={"Content-Type": "application/vnd.schemaregistry.v1+json"}, json=payload_data)
    if response.status_code == 200:
        return "IMPORTED"
    else:
        return response.content

def get_subject_paths(directory):
    fully_qualified_subjects = set()
    for root, dirs, files in os.walk(directory):
        if files:
            fully_qualified_subjects.add(root)
    return fully_qualified_subjects
    
def get_subjects_by_subject_path(subject_paths, import_context):
    subjects_by_path = {}
    for subject_path in subject_paths:
        context_parts = subject_path.split(os.path.sep)
        base_subject = context_parts[-1]
        
        context = [import_context] if import_context else []
        if "contexts" in context_parts:
            context_index = context_parts.index("contexts")
            context = context + context_parts[context_index + 1:-1]

        if context:
            subjects_by_path[subject_path] = ":." + '.'.join(context) + ":" + base_subject
        else:
            subjects_by_path[subject_path] = base_subject
    return subjects_by_path

def get_existing_subjects(url, username=None, password=None):
    api_url = f"{url}/subjects"
    response = requests.get(api_url, auth = (username, password))
    if response.status_code == 200:
        subjects = response.json()
        return subjects
    else:
        print(f"Failed to retrieve subjects. Status code: {response.status_code}. Please verify your connection details")
        sys.exit(1)

def get_existing_contexts(url, username=None, password=None):
    api_url = f"{url}/contexts"
    response = requests.get(api_url, auth=(username, password))
    
    if response.status_code == 200:
        contexts = response.json()
        cleaned_contexts = [context.lstrip('.') for context in contexts]
        return cleaned_contexts
    else:
        print(f"Failed to retrieve contexts. Status code: {response.status_code}")
        return None

def process_subject(url, username, password, subject_path, subject, indent = ""):
    version_results = {}
    print(f"{indent}Attempting to put {subject} into IMPORT mode")
    if put_subject_into_mode(url, username, password, subject, "IMPORT", indent):
        for filename in sorted(os.listdir(subject_path)):
            full_path = os.path.join(subject_path, filename)
            if (os.path.isfile(full_path)):
                print(f"{indent}\t- Processing file {full_path}")
                payload_data = read_schema_from_file(full_path)
                version = payload_data["version"]
                version_results[str(version)] = send_schema_to_registry(url, username, password, subject, payload_data)    
        put_subject_into_mode(url, username, password, subject, "READWRITE", indent)
    else:
        print(f"{indent}*** Unable to put subject {subject} into IMPORT mode. Not importing this subject ***")
        version_results["*"] = "FAILED"
    return version_results

def process_subjects(url, username, password, subjects_by_path):
    print("\n- Processing Subjects")
    results = {}
    for subject_path, subject in subjects_by_path.items():
        indent = "\t"
        print(f"{indent}Processing Subject {subject} with path {subject_path}")
        results[subject] = process_subject(url, username, password, subject_path, subject, f"{indent}\t")
        print("\n")
    return results

def import_schemas_to_registry(url, username, password, import_folder, import_context):
    subject_paths = get_subject_paths(os.path.join(import_folder))
    subjects_by_path = get_subjects_by_subject_path(subject_paths, import_context)
    results = process_subjects(url, username, password, subjects_by_path)
    print(f"Import Results: \n{results}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Schema Import Script")
    parser.add_argument("--url", required=True, help="URL of the registry")
    parser.add_argument("--username", help="Username for authentication [Optional]")
    parser.add_argument("--password", help="Password for authentication [Optional]")
    parser.add_argument("--import-folder", required=True, help="Folder containing schemas to import")
    parser.add_argument("--import-context", help="Provide a context for the imported schemas")

    args = parser.parse_args()
    url = args.url
    username = args.username
    password = args.password
    import_folder = args.import_folder
    import_context = args.import_context

    existing_subjects = get_existing_subjects(url, username, password)
    if existing_subjects and import_context == None:
        print("The target schema registry contains subjects and no import context has been provided")
        print("In order to prevent any unintended overwrites, if subjects already exist in a target registry, you must provide an import context using --import-context")
        print("Please note that the import context you provide must not already exist in the target registry")
        print("This script will now exit")
        sys.exit(1)
    
    if import_context:
        existing_contexts = get_existing_contexts(url, username, password)
        if import_context in existing_contexts:
            print(f"The import context you have provided: {import_context} already exists in the schema registry")
            print("In order to prevent any unintended overwrites, please provide a context that does not already exist")
            print("This script will now exit")
            sys.exit(1)

    import_schemas_to_registry(url, username, password, import_folder, import_context)