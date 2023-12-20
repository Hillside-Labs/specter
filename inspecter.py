# %%
#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import json
import yaml
import logging
from minifier import OpenAPIMinifierService

from llama_index.readers.schema.base import Document
from llama_index.llms import OpenAI
from llama_index import VectorStoreIndex, download_loader, \
    StorageContext, load_index_from_storage, ServiceContext, Prompt

file_dirs = [
    # "./data/do_openapi.yaml",
    "./data/stripe.yaml",
    # "./data/openai.yaml",
    # "./data/twitter.yaml",
    # "./data/adobe_aem.yaml"
]

endpoints, ep_by_method = OpenAPIMinifierService().run(
    [yaml.load(open(file_dir), Loader=yaml.Loader) for file_dir in file_dirs]
)

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
# this primer_prompt is giving weird responses

# Assuming 80% of the business comes from droplets, what is the most important API call to the business
# Customer or Business context?
query = "what is the most important API endpoint"

faq = [
    "what is the most important API endpoint",
    "",
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
    # Split the response by "Final Answer:"
    parts = model_response.split("Final Answer:")

    # Check if there are multiple occurrences of "Final Answer:"
    if len(parts) > 1:
        # Extract the content after the last "Final Answer:"
        logging.info(parts[0])
        final_answer = parts[-1].strip()
        return final_answer
    else:
        # If there is no "Final Answer:", return None or handle accordingly
        return None

model_name="gpt-4"
llm = OpenAI(temperature=0.5, model=model_name)
service_context = ServiceContext.from_defaults(llm=llm)

# %%
if not os.path.exists("./storage"):
    documents = load_data(ep_by_method["post"])
    index = VectorStoreIndex.from_documents(
        documents, service_context=service_context
    )
    index.storage_context.persist()
else:
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    index = load_index_from_storage(storage_context)

template = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    f"{primer_prompt}"
    f"{openapi_format_instructions}"
    "Given this information, please answer the question: {query_str}\n"
)
qa_template = Prompt(template)

query_engine = index.as_query_engine(text_qa_template=qa_template)

# from IPython.display import display, Markdown
# def display_prompt_dict(prompts_dict):
#     for k, p in prompts_dict.items():
#         text_md = f"**Prompt Key**: {k}<br>" f"**Text:** <br>"
#         display(Markdown(text_md))
#         print(p.get_template())
#         display(Markdown("<br><br>"))
# 
# display_prompt_dict(query_engine.get_prompts())
# response = query_engine.query(query)
# print(extract_final_answer(response.response))
# %%
