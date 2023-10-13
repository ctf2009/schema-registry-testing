import requests
import sys
import os
import json

def read_schema_from_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def put_subject_into_mode(url, username, password, subject, mode):
    mode_url = f"{url}/mode/{subject}"
    data = {
        "mode": mode
    }

    return requests.put(mode_url, auth=(username, password), headers={"Content-Type": "application/json"}, json=data)

def send_schema_to_registry(url, username, password, subject, payload_data):
    headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}

    #TODO: Complete this

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
    print("\n- Verifying existing subjects in registry")

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

def process_subjects(url, username, password, subjects_by_path):
    print("\n- Processing Subjects")
    for subject_path, subject in subjects_by_path.items():
        print(f"\tProcessing Subject {subject} with path {subject_path}")
        print(f"\t\tAttempting to put {subject} into IMPORT mode")
        response = put_subject_into_mode(url, username, password, subject, "IMPORT")
        if response.status_code == 200:
            print(f"\t\tSubject: {subject} is now in INPORT mode")
            for filename in sorted(os.listdir(subject_path)):
                full_path = os.path.join(subject_path, filename)
                if (os.path.isfile(full_path)):
                    print(f"\t\t\t- Processing file {full_path}")
                    schema = read_schema_from_file(full_path)
                    if "subject" in schema:
                        del schema["subject"]

                    payload_data = json.dumps(schema)
                    #send_schema_to_registry(url, username, password, subject, payload_data)

            print(f"\t\tReturning {subject} into READWRITE mode")
            response = put_subject_into_mode(url, username, password, subject, "READWRITE")
            if response.status_code != 200:
                print(f"\t\tUnable to transition Subject: {subject} to READWRITE mode")
        else:
            print(f"\t\tUnable to put subject {subject} into IMPORT mode. Not importing this subject")
        print("\n")

def import_schemas_to_registry(url, username, password, import_folder, force):

    subject_paths = get_subject_paths(os.path.join(import_folder))
    subjects_by_path = get_subjects_by_subject_path(subject_paths)

    verify_import_against_existing_subjects(url, username, password, list(subjects_by_path.values()), force)
    process_subjects(url, username, password, subjects_by_path)

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

    if force:
        user_input = input("The --force flag has been provided. To continue you must type 'Y' to confirm you understand the risks associated with this operation: ")

        if user_input.upper() == "Y":
            print("Continuing...")
        else:
            print("Exiting...")
            exit()

    import_schemas_to_registry(url, username, password, import_folder, force)
