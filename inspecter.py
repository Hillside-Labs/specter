# %%
import os, re
import json, yaml
from minifier import OpenAPIMinifierService

from textwrap import dedent

from llama_index.readers.schema.base import Document
from llama_index.llms import OpenAI
from llama_index import (
    VectorStoreIndex,
    download_loader,
    StorageContext,
    load_index_from_storage,
    ServiceContext
)

file_dirs = [
    "./data/do_openapi.yaml",
    # "./data/stripe.yaml",
    # "./data/openai.yaml",
    # "./data/twitter.yaml",
    # "./data/adobe_aem.yaml"
]

endpoints, ep_by_method = OpenAPIMinifierService().run(
    [yaml.load(open(file_dir), Loader=yaml.Loader) for file_dir in file_dirs]
)

x = dedent(
    """\
    Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action Input: what to instruct the AI Action representative.
Observation: The Agent's response
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer. User can't see any of my observations, API responses,
links, or tools.
Final Answer: the final answer to the original input question with the right amount of detail

When responding with your Final Answer, remember that the person you are responding to CANNOT
see any of your Thought/Action/Action Input/Observations, so if there is any relevant information
there you need to include it explicitly in your response.\n"""
)

# Provide examples
# Make sure to check you did not miss anything in the previous passes.
# Use a tool: code interpreter, specific functions, external APIs, etc

primer_prompt = """\
You are a documentation reading assistant. You help come up with very important insights \
and suggestions from a specification that describes API structure of a company \
like use-cases, cost prediction, value metrics, retention risk and sources of error. \
The audience is going to be the users of the API, which can range from a one-person company to a large corporation. \
Stay within the scope of the given API specification, if you do not know the answer to a question, respond by saying \
"I do not know the answer to your question." \
Be as detailed and thorough as possible, provide citations when necessary. \
Work out your own solution before rushing to conclusion.
Use inner monologue or sequence of queries to reach a conclusion. \

"""
# this primer_prompt is giving weird responses

# Assuming 80% of the business comes from droplets, what is the most important API call to the business
# Customer or Business context?
query = "what is the most important api in the given context for the customer, make some assumptions and state the assumptions"

faq = [
    "what is the most important api in the given context for the customer, make some assumptions and state the assumptions",
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

query_engine = index.as_query_engine()
response = query_engine.query(x + query)
print(response.response)