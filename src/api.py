import requests
from urllib3.util import Retry


class Api(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.path = ""

        adapter = requests.adapters.HTTPAdapter(
            max_retries=Retry(total=10, backoff_factor=0.1)
        )

        self.r = requests.Session()
        self.r.mount("http://", adapter)
        self.r.mount("https://", adapter)

    def __url(self, resource="", id_var=None):
        address = (
            self.address
            if self.address.startswith("http")
            else "http://" + self.address
        )
        id_var_path = f"/{id_var}" if id_var else ""

        return f"{address}:{self.port}{self.path}{resource}{id_var_path}"

    def __get(self, resource, id_var=None):
        response = self.r.get(self.__url(resource, id_var))
        status_code = response.status_code

        if id_var:
            id_var_string = f" {id_var}"
        else:
            id_var_string = ""

        print(f"Fetching {resource}{id_var_string}: {status_code}")
        if status_code > 300:
            print(response.json())
            print("\n")

        if status_code < 300:
            return response.json()

    def __create(self, resource, body):
        response = self.r.post(self.__url(resource), json=body)
        status_code = response.status_code

        if status_code < 300:
            print(f"Creating {resource} {response.json()['id']}: {status_code}")
        else:
            print(f"Creating {resource}: {status_code}")

        if status_code > 300:
            print(response.json())
            print("\n")

    def __edit(self, resource, body, id_var=None):
        old_version = self.__get(resource, id_var)

        for key in body:
            old_version[key] = body[key]

        response = self.r.put(self.__url(resource, id_var), json=old_version)
        status_code = response.status_code

        if id_var:
            id_var_string = f" {id_var}"
        else:
            id_var_string = ""

        print(f"Editing {resource}{id_var_string}: {status_code}")

        if status_code > 300:
            print(response.json())
            print("\n")

    def __delete(self, resource, id_var):
        status_code = self.r.delete(self.__url(resource, id_var)).status_code
        print(f"Deleting {resource} {id_var}: {status_code}")

    def __triage_and_apply(self, object, resource=""):
        if isinstance(object, dict):
            if any(isinstance(object[key], (dict, list)) for key in object):
                for key in object:
                    self.__triage_and_apply(object[key], f"{resource}/{key}")
            else:
                self.__edit(resource, object)
        else:
            for body in object:
                self.__create(resource, body)

    def initialize(self):
        response = self.r.get(f"{self.__url()}/initialize.js")

        bits = response.text.split("'")
        api_root = bits[1]
        api_key = bits[3]

        self.path = api_root
        self.r.headers.update({"X-Api-Key": api_key})

        print("Successfully connected to the server and fetched the API key and path")

    def apply(self, config):
        self.__triage_and_apply(config)
