# %%
#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import json
import yaml
import logging
import requests
from minifier import OpenAPIMinifierService

from llama_index.readers.schema.base import Document
from llama_index.llms import OpenAI
from llama_index import VectorStoreIndex, download_loader, \
    StorageContext, load_index_from_storage, ServiceContext, Prompt

def load_yaml_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        yaml_data = yaml.safe_load(response.content.decode('utf-8'))
        return yaml_data
    else:
        print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
        return None

url = input("Enter your OpenAPI specification yaml url:\n")

print("Enter information related to the business:")

audience = input("the audience is: ")
use_cases = input("use-cases are: ")
comments = input("any other comments (for example, weightage is given to certain aspect): ")
context = f"The audience for the given API pecification is {audience}, use-cases are {use_cases}. \
Other things to note are {comments}"

endpoints, ep_by_method = OpenAPIMinifierService().run([load_yaml_from_url(url)])

openapi_format_instructions = """Use the following format:
```
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take
Action Input: what to instruct the AI Action representative.
Observation: The Agent's response
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer. User can't see any of my observations, API responses, links, or tools.
Final Answer: the final answer to the original input question in markdown.
```
Please ALWAYS start with a Thought.
"""

primer_prompt = """\
You are a documentation reading assistant. You help come up with very important insights \
and suggestions from a specification that describes API structure of a company \
like use-cases, cost prediction, value metrics, retention risk and sources of error. \
The audience is going to be the users of the API, which can range from a one-person company to a large corporation. \
Stay within the scope of the given API specification, if you do not know the answer to a question, respond by saying \
"I do not know the answer to your question." \
Work out your own solution before rushing to conclusion. \
Use inner monologue or sequence of queries to reach a conclusion. \
Give usage details and examples when discussing an API endpoint.
"""

faq = [
    "What is the most important API endpoint?",
    "What is a potential chokepoint for our customers?",
    "Which APIs have to be monitored for cost optimization?",
    "What are the sources of potential customer retention risk?"
]

JsonDataReader = download_loader("JsonDataReader")
loader = JsonDataReader()

def load_data(input_data: list[dict]):
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

model_name="gpt-4"
llm = OpenAI(temperature=0.2, model=model_name)
service_context = ServiceContext.from_defaults(llm=llm)

# %%
def sanitize(url):
    valid_chars = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*').findall(url)
    return ''.join(valid_chars)

persist_dir = f"./storage/{sanitize(url)}"

if not os.path.exists(persist_dir):
    documents = load_data(ep_by_method["post"])
    index = VectorStoreIndex.from_documents(
        documents, service_context=service_context
    )
    index.storage_context.persist(persist_dir)
else:
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    index = load_index_from_storage(storage_context)

template = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    f"{primer_prompt}"
    f"{context}"
    f"{openapi_format_instructions}"
    "Given this information, please answer the question: {query_str}\n"
)
qa_template = Prompt(template)

query_engine = index.as_query_engine(text_qa_template=qa_template)

for q in faq:
    response = query_engine.query(q)
    print("Query:", q)
    print("Final Answer:", extract_final_answer(response.response))
    print()