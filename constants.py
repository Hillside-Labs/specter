from llama_index import Prompt

openapi_format_instructions = """\
Use the following format:
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


def create_business_context(audience, use_cases, comments):
    ctx = "For the given API specification,"
    if audience:
        ctx += f"audience is {audience}, "
    if use_cases:
        ctx += f"use-cases are {use_cases}, "
    if comments:
        ctx += f"other things to note are {comments}."
    return ctx


def create_qa_template(primer_prompt, context, openapi_format_instructions):
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

    return Prompt(template)


FAQ = [
    "What is the most important API endpoint?",
    "What is a potential chokepoint for our customers?",
    "Which APIs have to be monitored for cost optimization?",
    "What are the sources of potential customer retention risk?",
]
