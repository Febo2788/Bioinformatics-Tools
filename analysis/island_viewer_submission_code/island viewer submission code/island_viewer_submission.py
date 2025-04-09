import os
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from tkinter import filedialog
from tkinter import Tk

server = "https://www.pathogenomics.sfu.ca/islandviewer"
ext = "/rest/submit/"

root = Tk()
root.withdraw()
folder_selected = filedialog.askdirectory()
print(f"Selected folder: {folder_selected}")

responses = []

for filename in os.listdir(folder_selected):
    if filename.endswith(".genbank") or filename.endswith(".gkb"):
        filepath = os.path.join(folder_selected, filename)
        print(f"Submitting {filepath}...")

        multipart_data = MultipartEncoder(
            fields={
                "format_type": "GENBANK",
                'email_addr': 'thoracicformula@gmail.com',
                'genome_file': ('filename', open(filepath, 'rb'), 'text/plain')}
        )
        headers = {
            'Content-Type': multipart_data.content_type
            # if you get an auth token later, you can add it here
            # 'x-authtoken': auth_token
        }

        response = requests.post(server + ext, headers=headers, data=multipart_data)

        if not response.ok:
            print(f"Error submitting {filepath}: {response.status_code} {response.reason}")
        else:
            decoded = response.json()
            print(repr(decoded))
            responses.append(repr(decoded))

with open("C:/Users/thora/Downloads/job_ids.txt", "a") as file:
    for resp in responses:
        file.write(f"{resp}\n")
