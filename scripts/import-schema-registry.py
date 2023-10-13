import requests
import sys
import os

def read_schema_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

#def get_subject_from_path(file_path):
#    return os.path.basename(os.path.dirname(file_path))
#
#def get_version_from_path(file_path):
#    return os.path.splitext(os.path.basename(file_path))[0]
#

def put_subject_into_mode(url, username, password, subject, mode):
    mode_url = f"{url}/mode/{subject}"
    data = {
        "mode": mode
    }

    return requests.put(mode_url, auth=(username, password), headers={"Content-Type": "application/json"}, json=data)

def registry_has_subjects(url, username, password):
    subjects_url = f"{url}/subjects"
    response = requests.get(subjects_url, auth=(username, password))
    return response.status_code == 200 and len(response.json()) > 0

def send_schema_to_registry(url, username, password, schema, subject, context=None):
    headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}

    if context:
        subject_url = f"{url}/subjects/{context}"
        data = {"schema": schema}
    else:
        subject_url = f"{url}/subjects/{subject}"
        data = {"schema": schema}


    print(f"url is {url}")
    print(f"subject is {subject}")
    print(f"context is {context}")
    print(f"schema is {schema}")

    #response = requests.post(subject_url, headers=headers, data=data, auth=(username, password))

    #if response.status_code == 200:
    #    print(f"Imported schema for subject: {subject}")
    #else:
    #    print(f"Failed to import schema for subject: {subject}. Status code: {response.status_code}")

def get_import_files(import_folder):
    files = []
    for root, _, filenames in os.walk(import_folder):
        files.extend(os.path.join(root, filename) for filename in filenames)
    return files

def get_subject_paths(directory):
    fully_qualified_subjects = set()
    for root, dirs, files in os.walk(directory):
        if files:
            fully_qualified_subjects.add(root)
    return fully_qualified_subjects
    
def get_subjects_by_subject_path(subject_paths):
    subjects_by_path = {}

    for subject_path in subject_paths:
        context_parts = subject_path.split(os.path.sep)
        base_subject = context_parts[-1]
        if "contexts" in context_parts:
            context_index = context_parts.index("contexts")
            context = context_parts[context_index + 1:-1]
            if context:
                subjects_by_path[subject_path] = ":." + '.'.join(context) + ":" + base_subject
                continue

        subjects_by_path[subject_path] = base_subject
    return subjects_by_path

def get_subjects_list(url, username=None, password=None):
    api_url = f"{url}/subjects"
    auth = None

    if username and password:
        auth = (username, password)

    response = requests.get(api_url, auth=auth)

    if response.status_code == 200:
        subjects = response.json()
        return subjects
    else:
        print(f"Failed to retrieve subjects. Status code: {response.status_code}")
        return None

def verify_import_against_existing_subjects(url, username, password, fully_qualified_subjects, force):
    print("\nVerifying existing subjects in registry")

    existing_subjects = get_subjects_list(url, username, password)
    print(f"\tExisting Subjects in Target Registry: {existing_subjects}")

    intersected_subjects = []
    for subject in fully_qualified_subjects:
        if subject in existing_subjects:
            intersected_subjects.append(subject)

    if intersected_subjects:
        if not force:
            print("\n\tThere were subjects in the target registry matching subjects in the import")
            print("\tEither provide an additional context with the --additional-context param")
            print("\tOr you can force the import. Please note that this option will overwrite any existing subjects where there is a match")
            print(f"\n\tConflicting Subjects: {intersected_subjects}")
            sys.exit(1)

    print("\tVerification complete")

def import_schemas_to_registry(url, username, password, import_folder, force):
    if force:
        user_input = input("The --force flag has been provided. To continue you must type 'Y' to confirm you understand the risks associated with this operation: ")

        if user_input.upper() == "Y":
            print("Continuing...")
        else:
            print("Exiting...")
            exit()

    subject_paths = get_subject_paths(os.path.join(import_folder))
    subjects_by_path = get_subjects_by_subject_path(subject_paths)

    verify_import_against_existing_subjects(url, username, password, list(subjects_by_path.values()), force)
    
   #for file_path in files:

   #    print(f"\nProcessing File Path: {file_path}")
   #    context = get_context_from_path(file_path)
   #    subject = get_subject_from_path(file_path)
   #    version = get_version_from_path(file_path)

   #    #print(f"Derived Context is {context}")
        #print(f"Derived Subject is {subject}")
        #print(f"Derived Version is {version}")
#
        ## Check if the subject exists in the registry
        #subject_url = f"{url}/subjects/{subject}/versions"
        #response = requests.get(subject_url, auth=(username, password))
#
        #if response.status_code == 404 or force:
        #    # Subject doesn't exist or force flag is set
        #    schema = read_schema_from_file(file_path)
        #    send_schema_to_registry(url, username, password, schema, subject, context)
        #elif not force:
        #    print(f"Subject {subject} already exists with version. Use --force flag to override or provide an additional context")

if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 6:
        print("Usage: python import-script.py <URL> <username> <password> --import-folder <import_folder> [--force]")
        sys.exit(1)

    url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    import_folder = None
    force = False

    if "--import-folder" in sys.argv:
        import_index = sys.argv.index("--import-folder")
        if import_index + 1 < len(sys.argv):
            import_folder = sys.argv[import_index + 1]

    if "--force" in sys.argv:
        force = True

    if not import_folder:
        print("Please provide the --import-folder parameter.")
        sys.exit(1)

    import_schemas_to_registry(url, username, password, import_folder, force)
