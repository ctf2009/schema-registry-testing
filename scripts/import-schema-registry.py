import requests
import sys
import os

def put_subject_into_mode(url, username, password, subject, mode):
    # Define the API endpoint for putting a subject into the specified mode
    mode_url = f"{url}/mode/{subject}?force=true"

    print(f"{mode_url}")

    # Define the data to send in the request
    data = {
        "mode": mode
    }

    # Make a PUT request to set the subject to the specified mode
    response = requests.put(mode_url, auth=(username, password), headers={"Content-Type": "application/json"}, json=data)

    return response

def import_schemas_from_folder(url, username, password, import_folder):
    # Define the API endpoint for registering schemas
    register_url = f"{url}/subjects"

    # Check if the import folder exists
    if not os.path.exists(import_folder):
        print(f"Import folder '{import_folder}' does not exist.")
        return

    # List all subject folders in the import folder
    subject_folders = [folder for folder in os.listdir(import_folder) if os.path.isdir(os.path.join(import_folder, folder))]

    for subject in subject_folders:
        subject_folder = os.path.join(import_folder, subject)
        schema_files = [f for f in os.listdir(subject_folder) if os.path.isfile(os.path.join(subject_folder, f))]

        for schema_file in schema_files:
            print(f"Importing schema file {schema_file}")
            #version = os.path.splitext(schema_file)[0]
            #schema_path = os.path.join(subject_folder, schema_file)
#
            #with open(schema_path, 'r') as file:
            #    schema = file.read()
#
            ## Create the subject with the schema version
            #headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
            #data = {
            #    "schema": schema,
            #    "schemaType": "JSON"
            #}
#
            #response = requests.post(f"{register_url}/{subject}/versions", auth=(username, password), headers=headers, json=data)
#
            #if response.status_code == 200:
            #    print(f"Registered version {version} of {subject}")
            #else:
                #print(f"Failed to register version {version} of {subject}. Status code: {response.status_code}")

if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 6:
        print("Usage: python import-schemas-to-registry.py <URL> <username> <password> --import-folder <import_folder>")
        sys.exit(1)

    url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    import_folder = None

    if "--import-folder" in sys.argv:
        import_index = sys.argv.index("--import-folder")
        if import_index + 1 < len(sys.argv):
            import_folder = sys.argv[import_index + 1]

    if import_folder:
        # List all subject folders in the import folder
        subject_folders = [folder for folder in os.listdir(import_folder) if os.path.isdir(os.path.join(import_folder, folder))]

        for subject in subject_folders:
            print(f"\nPutting subject '{subject}' into IMPORT mode...")

            response = put_subject_into_mode(url, username, password, subject, "IMPORT")

            if response.status_code == 200:
                print(f"Subject '{subject}' is now in IMPORT mode.")
                import_schemas_from_folder(url, username, password, os.path.join(import_folder, subject))

                print(f"Taking subject '{subject}' out of IMPORT mode...")
                response = put_subject_into_mode(url, username, password, subject, "READWRITE")

                if response.status_code == 200:
                    print(f"Subject '{subject}' is now in READWRITE mode.")
                else:
                    print(f"Failed to put subject '{subject}' into READWRITE mode. Status code: {response.status_code}")
            else:
                print(f"Failed to put subject '{subject}' into IMPORT mode. Status code: {response.status_code}")
                sys.exit(1)
    else:
        print("Please specify the --import-folder parameter.")
