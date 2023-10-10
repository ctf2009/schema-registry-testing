import requests
import sys
import os

def get_subjects_list(url, username=None, password=None):
    # Define the API endpoint for getting the list of subjects
    api_url = f"{url}/subjects"

    # Prepare authentication if username and password are provided
    auth = None
    if username and password:
        auth = (username, password)

    # Make a GET request with optional basic authentication
    response = requests.get(api_url, auth=auth)

    if response.status_code == 200:
        subjects = response.json()
        return subjects
    else:
        print(f"Failed to retrieve subjects. Status code: {response.status_code}")
        return None

def save_schema_to_file(export_folder, subject, version, schema):
    folder_name = os.path.join(export_folder, subject)
    file_name = f"{subject}-{version}.json"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    with open(os.path.join(folder_name, file_name), 'w') as file:
        file.write(schema)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 5:
        print("Usage: python script.py <URL> [username] [password] [--export <export_folder>]")
        sys.exit(1)

    url = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) >= 3 else None
    password = sys.argv[3] if len(sys.argv) >= 4 else None
    export_folder = "export"  # Default export folder

    if "--export" in sys.argv:
        export_index = sys.argv.index("--export")
        if export_index + 1 < len(sys.argv):
            export_folder = sys.argv[export_index + 1]

    subjects = get_subjects_list(url, username, password)
    print(f"There are {len(subjects)} subjects: {subjects}")

    if subjects:
        for subject in subjects:
            print(f"Processing subject: {subject}")
            versions_url = f"{url}/subjects/{subject}/versions"
            versions_response = requests.get(versions_url, auth=(username, password))

            if versions_response.status_code == 200:
                versions = versions_response.json()
                print(f"Versions found for subject [{subject}]: {versions}")
 
                for version in versions:
                    schema_url = f"{url}/subjects/{subject}/versions/{version}" 
                    schema_response = requests.get(schema_url, auth=(username, password))
                    if schema_response.status_code == 200:
                        schema = schema_response.text
                        save_schema_to_file(export_folder, subject, version, schema)
                        print(f"Saved version {version} to {export_folder}/{subject}/{version}.json")
                    else:
                       print(f"Failed to retrieve schema for version {version}. Status code: {schema_response.status_code}")
            else:
                print(f"Failed to retrieve versions for subject {subject}. Status code: {versions_response.status_code}")
