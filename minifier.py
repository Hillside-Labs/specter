import string, re
from urllib.parse import urlparse
from collections import defaultdict

class OpenAPIMinifierService:
    def __init__(self):
        self.operationID_counter = 0

        self.keys_to_keep = {
            "parameters": True,
            "good_responses": True,
            "bad_responses": False,
            "request_bodies": True,
            "schemas": True,
            "endpoint_descriptions": True,
            "endpoint_summaries": True,
            "enums": False,
            "nested_descriptions": True,
            "examples": False,
            "tag_summaries": False,
            "deprecated": False,
        }
        self.methods_to_handle = {"get", "post", "patch", "delete"}
        self.key_abbreviations = {
            "operationid": "opid",
            "parameters": "params",
            "requestbody": "reqBody",
            "properties": "props",
            "schemaname": "schName",
            "description": "desc",
            "summary": "sum",
            "string": "str",
            "number": "num",
            "object": "obj",
            "boolean": "bool",
            "array": "arr",
            "object": "obj",
        }

        self.key_abbreviations_enabled = True

    def run(self, open_api_specs):
        full_open_api_specs = self.create_full_spec(open_api_specs)

        minified_endpoints, endpoints_by_method = self.minify(full_open_api_specs)

        minified_endpoints = sorted(
            minified_endpoints, key=lambda x: (x["tag"], x["operation_id"])
        )

        minified_endpoints = self.create_endpoint_documents(
            minified_endpoints, full_open_api_specs
        )

        return [minified_endpoints, endpoints_by_method]

    def create_full_spec(self, open_api_specs):
        merged_open_api_spec = None

        for open_api_spec in open_api_specs:
            if merged_open_api_spec is None:
                merged_open_api_spec = open_api_spec
            else:
                merged_open_api_spec["paths"].update(open_api_spec["paths"])

                if "components" in open_api_spec:
                    if "components" not in merged_open_api_spec:
                        merged_open_api_spec["components"] = {}
                    for component_type, components in open_api_spec[
                        "components"
                    ].items():
                        if component_type not in merged_open_api_spec["components"]:
                            merged_open_api_spec["components"][component_type] = {}
                        merged_open_api_spec["components"][component_type].update(
                            components
                        )

        merged_open_api_spec["paths"] = dict(
            sorted(merged_open_api_spec["paths"].items())
        )
        if "components" in merged_open_api_spec:
            for component_type in merged_open_api_spec["components"]:
                merged_open_api_spec["components"][component_type] = dict(
                    sorted(merged_open_api_spec["components"][component_type].items())
                )


        return merged_open_api_spec

    def minify(self, open_api_spec):
        server_url = open_api_spec["servers"][0]["url"]

        minified_endpoints = []
        endpoints_by_method = defaultdict(list)

        for path, methods in open_api_spec["paths"].items():
            for method, endpoint in methods.items():
                if method not in self.methods_to_handle:
                    continue
                if (
                    endpoint.get("deprecated", False)
                    and not self.keys_to_keep["deprecated"]
                ):
                    continue

                if self.keys_to_keep["schemas"]:
                    extracted_endpoint_data = self.resolve_refs(open_api_spec, endpoint)
                else:
                    extracted_endpoint_data = endpoint

                extracted_endpoint_data = self.populate_keys(
                    extracted_endpoint_data, path
                )

                extracted_endpoint_data = self.remove_empty_keys(
                    extracted_endpoint_data
                )

                extracted_endpoint_data = self.remove_unnecessary_keys(
                    extracted_endpoint_data
                )

                extracted_endpoint_data = self.flatten_endpoint(extracted_endpoint_data)

                if self.key_abbreviations_enabled:
                    extracted_endpoint_data = self.abbreviate(
                        extracted_endpoint_data, self.key_abbreviations
                    )

                tags = endpoint.get("tags", [])
                tag = tags[0] if tags else "default"

                operation_id = endpoint.get("operationId", "")
                processed_endpoint = self.write_dict_to_text(extracted_endpoint_data)
                content_string = f"operationId: {operation_id} path: {server_url}{path} content: {processed_endpoint}"


                endpoint_dict = {
                    "tag": tag,
                    "operation_id": operation_id,
                    "server_url": f"{server_url}{path}",
                    "content": content_string,
                }
                endpoints_by_method[method].append(endpoint_dict)
                minified_endpoints.append(endpoint_dict)

        return [minified_endpoints, endpoints_by_method]

    def resolve_refs(self, open_api_spec, endpoint):
        if isinstance(endpoint, dict):
            new_endpoint = {}
            for key, value in endpoint.items():
                if key == "$ref":
                    ref_path = value.split("/")[1:]
                    ref_object = open_api_spec
                    for p in ref_path:
                        ref_object = ref_object.get(p, {})

                    ref_object = self.resolve_refs(open_api_spec, ref_object)

                    new_key = ref_path[-1]
                    new_endpoint[new_key] = ref_object
                else:
                    new_endpoint[key] = self.resolve_refs(open_api_spec, value)
            return new_endpoint

        elif isinstance(endpoint, list):
            return [self.resolve_refs(open_api_spec, item) for item in endpoint]

        else:
            return endpoint

    def populate_keys(self, endpoint, path):
        extracted_endpoint_data = {}

        if self.keys_to_keep["parameters"]:
            extracted_endpoint_data["parameters"] = endpoint.get("parameters")

        if self.keys_to_keep["endpoint_summaries"]:
            extracted_endpoint_data["summary"] = endpoint.get("summary")

        if self.keys_to_keep["endpoint_descriptions"]:
            extracted_endpoint_data["description"] = endpoint.get("description")

        if self.keys_to_keep["request_bodies"]:
            extracted_endpoint_data["requestBody"] = endpoint.get("requestBody")

        if self.keys_to_keep["good_responses"] or self.keys_to_keep["bad_responses"]:
            extracted_endpoint_data["responses"] = {}

        if self.keys_to_keep["good_responses"]:
            if "responses" in endpoint and "200" in endpoint["responses"]:
                extracted_endpoint_data["responses"]["200"] = endpoint["responses"].get("200")

        if self.keys_to_keep["bad_responses"]:
            if "responses" in endpoint:
                for status_code, response in endpoint["responses"].items():
                    if (
                        status_code.startswith("4")
                        or status_code.startswith("5")
                        or "default" in status_code
                    ):
                        bad_response_content = response
                        if bad_response_content is not None:
                            extracted_endpoint_data["responses"][
                                f"{status_code}"
                            ] = bad_response_content

        return extracted_endpoint_data

    def remove_empty_keys(self, endpoint):
        if isinstance(endpoint, dict):
            new_endpoint = {}
            for key, value in endpoint.items():
                if value is not None and value != "":
                    cleaned_value = self.remove_empty_keys(value)
                    new_endpoint[key] = cleaned_value
            return new_endpoint
        elif isinstance(endpoint, list):
            return [self.remove_empty_keys(item) for item in endpoint]
        else:
            return endpoint

    def remove_unnecessary_keys(self, endpoint):
        stack = [(endpoint, [])]

        while stack:
            current_data, parent_keys = stack.pop()

            if isinstance(current_data, dict):
                for k in list(current_data.keys()):
                    if k == "example" and not self.keys_to_keep["examples"]:
                        del current_data[k]
                    if k == "enum" and not self.keys_to_keep["enums"]:
                        del current_data[k]
                    elif (
                        k == "description"
                        and len(parent_keys) > 0
                        and not self.keys_to_keep["nested_descriptions"]
                    ):
                        del current_data[k]
                    if k in current_data and isinstance(current_data[k], (dict, list)):
                        stack.append((current_data[k], parent_keys + [k]))

            elif isinstance(current_data, list):
                for item in current_data:
                    if isinstance(item, (dict, list)):
                        stack.append((item, parent_keys + ["list"]))

        return endpoint

    def flatten_endpoint(self, endpoint):
        if not isinstance(endpoint, dict):
            return endpoint

        flattened_endpoint = {}

        keep_keys = {"responses", "default", "200"}

        for key, value in endpoint.items():
            if isinstance(value, dict):
                if key in keep_keys or (
                    isinstance(key, str)
                    and (key.startswith("5") or key.startswith("4"))
                ):
                    flattened_endpoint[key] = self.flatten_endpoint(value)
                else:
                    while isinstance(value, dict) and len(value) == 1:
                        key, value = next(iter(value.items()))
                    flattened_endpoint[key] = self.flatten_endpoint(value)
            else:
                flattened_endpoint[key] = value

        return flattened_endpoint

    def abbreviate(self, data, abbreviations):
        if isinstance(data, dict):
            return {
                abbreviations.get(key.lower(), key.lower()): self.abbreviate(
                    abbreviations.get(str(value).lower(), value), abbreviations
                )
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.abbreviate(item, abbreviations) for item in data]
        elif isinstance(data, str):
            return abbreviations.get(data.lower(), data.lower())
        else:
            return data

    def create_endpoint_documents(self, minified_endpoints, open_api_spec):
        tag_summaries = self.get_tag_summaries(minified_endpoints, open_api_spec)

        for endpoint in minified_endpoints:
            tag = endpoint.get("tag") or "default"

            tag_summary_list = [
                summary for summary in tag_summaries if summary["name"] == tag
            ]
            tag_summary = tag_summary_list[0]["summary"] if tag_summary_list else ""
            tag_number = tag_summary_list[0]["tag_number"] if tag_summary_list else 0

            endpoint["tag_summary"] = tag_summary
            endpoint["tag_number"] = tag_number

            endpoint["doc_number"] = self.operationID_counter

            parsed = urlparse(endpoint["server_url"])
            if parsed.scheme and parsed.netloc:
                endpoint["title"] = re.sub(
                    r"https?://[^/]+/", "", endpoint["server_url"]
                )

            else:
                endpoint["title"] = {endpoint["server_url"]}

            filename = f"{tag_number}_{endpoint['tag']}_{endpoint['operation_id']}_{self.operationID_counter}"
            endpoint["filename"] = filename

            self.operationID_counter += 1

        return minified_endpoints

    def get_tag_summaries(self, minified_endpoints, open_api_spec):
        tag_summaries = []

        root_tags = open_api_spec.get("tags")
        if root_tags:
            for tag in root_tags:
                if tag not in [t["name"] for t in tag_summaries]:
                    name = tag.get("name")
                    summary = tag.get("description")
                    if name and summary:
                        tag_summaries.append(
                            {"name": name, "summary": self.write_dict_to_text(summary)}
                        )
                    else:
                        tag_summaries.append({"name": name, "summary": ""})

        for endpoint in minified_endpoints:
            tag = endpoint.get("tag") or "default"
            if tag not in [t["name"] for t in tag_summaries]:
                tag_summaries.append({"name": tag, "summary": ""})

        tag_summaries = sorted(tag_summaries, key=lambda x: (x["name"]))

        for i, tag in enumerate(tag_summaries):
            tag["tag_number"] = i

        return tag_summaries

    def write_dict_to_text(self, data):
        def remove_html_tags_and_punctuation(input_str):
            no_html_str = re.sub("<.*?>", "", input_str)
            modified_punctuation = set(string.punctuation) - {"/", "#"}
            return (
                "".join(ch for ch in no_html_str if ch not in modified_punctuation)
                .lower()
                .strip()
            )

        formatted_text_parts = []

        if isinstance(data, dict):
            for key, value in data.items():
                key = remove_html_tags_and_punctuation(key)

                if isinstance(value, (dict, list)):
                    formatted_text_parts.append(key)
                    formatted_text_parts.append(self.write_dict_to_text(value))
                else:
                    value = remove_html_tags_and_punctuation(str(value))
                    formatted_text_parts.append(f"{key} {value}")
        elif isinstance(data, list):
            for item in data:
                formatted_text_parts.append(self.write_dict_to_text(item))
        else:
            data = remove_html_tags_and_punctuation(str(data))
            formatted_text_parts.append(data)

        return "\n".join(filter(lambda x: x.strip(), formatted_text_parts))