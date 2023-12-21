#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import json
import yaml
import logging
import requests

import constants
from minifier import OpenAPIMinifierService

from llama_index.llms import OpenAI
from llama_index.readers.schema.base import Document
from llama_index import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    ServiceContext,
)


def load_from_spec_url(url, data_format):
    response = requests.get(url)

    if response.status_code == 200:
        if data_format == "yaml":
            return yaml.safe_load(response.content.decode("utf-8"))
        elif data_format == "json":
            return response.json()
    else:
        print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
        return None


def download_json_data(input_data: list[dict]):
    loaded = []

    for data in input_data:
        json_output = json.dumps(data, indent=0)
        lines = json_output.split("\n")
        useful_lines = [line for line in lines if not re.match(r"^[{}\[\],]*$", line)]
        loaded.append(Document(text="\n".join(useful_lines)))
    return loaded


def extract_final_answer(model_response):
    parts = model_response.split("Final Answer:")

    if len(parts) > 1:
        logging.info(parts[0])
        final_answer = parts[-1].strip()
        return final_answer
    else:
        return None


def sanitize_path(url):
    valid_chars = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*").findall(url)
    return "".join(valid_chars)


def load_documents_and_create_index(ep_by_method, persist_dir, service_context):
    if not os.path.exists(persist_dir):
        documents = download_json_data(ep_by_method["post"])
        index = VectorStoreIndex.from_documents(
            documents, service_context=service_context
        )
        index.storage_context.persist(persist_dir)
    else:
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)

    return index


def main(data_format, spec_url, audience, use_cases, comments):
    ep_by_method = OpenAPIMinifierService().run(
        [load_from_spec_url(spec_url, data_format)]
    )
    persist_dir = f"./storage/{sanitize_path(spec_url)}"
    service_context = ServiceContext.from_defaults(
        llm=OpenAI(temperature=0.2, model="gpt-4")
    )

    index = load_documents_and_create_index(ep_by_method, persist_dir, service_context)

    context = constants.create_business_context(audience, use_cases, comments)
    qa_template = constants.create_qa_template(
        constants.primer_prompt, context, constants.openapi_format_instructions
    )
    query_engine = index.as_query_engine(text_qa_template=qa_template)

    final_response = ""
    for que in constants.FAQ:
        response = query_engine.query(que)
        final_response += (
            f"Query: {que}\n"
            f"Final Answer: {extract_final_answer(response.response)}\n\n"
        )
    return final_response


if __name__ == "__main__":
    
    data_format = input("Type yaml or json: ")
    url = input("Enter your OpenAPI specification url:\n")

    print("Enter information related to the business:")
    
    audience = input("The audience is: ")
    use_cases = input("Use-cases are: ")
    comments = input("Any other comments (for example, weightage to be given to a certain aspect): ")

    print(main(data_format, url, audience, use_cases, comments))
