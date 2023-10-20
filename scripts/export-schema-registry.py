import requests
import sys
import os
import re
import argparse
from urllib3.exceptions import InsecureRequestWarning

ssl_verification=True

def get_subjects_list(url, username=None, password=None):
    api_url = f"{url}/subjects"
    auth = None

    if username and password:
        auth = (username, password)

    response = requests.get(api_url, auth=auth, verify=ssl_verification)

    if response.status_code == 200:
        subjects = response.json()
        return subjects
    else:
        print(f"Failed to retrieve subjects. Status code: {response.status_code}")
        return None

def extract_subject_base(subject):
    parts = subject.split(':')
    last_part = parts[-1]
    return last_part

def get_context(subject):
    match = re.match(r":\.(.+?):", subject)
    if match:
        return match.group(1)
    else:
        return None

def save_schema_to_file(filepath, schema):
    dirs =  os.path.dirname(filepath)

    if not os.path.exists(dirs):
        os.makedirs(dirs)

    with open(filepath, 'w') as file:
        file.write(schema)


def build_subject_folder_name(export_folder, subject):
    base_subject = extract_subject_base(subject)
    context = get_context(subject)

    if context:
        context_path = context.split(".")
        return os.path.join(export_folder, "contexts", *context_path, base_subject)
    else:
        return  os.path.join(export_folder, "default", base_subject)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Schema Export Script")
    parser.add_argument("--url", required=True, help="URL of the registry")
    parser.add_argument("--username", help="Username for authentication [Optional]")
    parser.add_argument("--password", help="Password for authentication [Optional]")
    parser.add_argument("--export-folder", default="export", help="Folder to export schemas to")
    parser.add_argument("--insecure", action='store_true', help="Provide this flag is you want do not want to use SSL Verification")

    args = parser.parse_args()
    url = args.url
    username = args.username
    password = args.password
    export_folder = args.export_folder
    insecure = args.insecure

    print(url)
    print(username)
    print(password)
    print(export_folder)
    print(insecure)

    if insecure:
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        ssl_verification=False

    subjects = get_subjects_list(url, username, password)
    print(f"There are {len(subjects)} subjects: {subjects}")

    if subjects:
        for subject in subjects:
            print(f"\nProcessing subject: {subject}")
            versions_url = f"{url}/subjects/{subject}/versions"
            versions_response = requests.get(versions_url, auth=(username, password), verify=ssl_verification)

            if versions_response.status_code == 200:
                versions = versions_response.json()
                print(f"Versions found for subject [{subject}]: {versions}")
 
                for version in versions:
                    schema_url = f"{url}/subjects/{subject}/versions/{version}" 
                    schema_response = requests.get(schema_url, auth=(username, password), verify=ssl_verification)
                    if schema_response.status_code == 200:
                        schema = schema_response.text
                        filepath = os.path.join(build_subject_folder_name(export_folder, subject), f"{version}.json")
                        save_schema_to_file(filepath, schema)
                        print(f"Saved version {version} to {filepath}")
                    else:
                       print(f"Failed to retrieve schema for version {version}. Status code: {schema_response.status_code}")
            else:
                print(f"Failed to retrieve versions for subject {subject}. Status code: {versions_response.status_code}")
