from flask import Flask, request
from main import main

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<h1>This is Specter by Hillside Labs</h1><p>Analyse your API specification (OAS) to draw important observations</p>"


# todo: add validations and input sanitization in body
# use templates to render html from analyse function
# add an input form html on landing page
# deploy to fly
@app.route("/analyse", methods=["POST"])
def analyse():
    body = request.get_json()
    return main(
        body["data_format"],
        body["spec_url"],
        body["audience"] if "audience" in body else "",
        body["use_cases"] if "use_cases" in body else "",
        body["comments"] if "comments" in body else "",
    )
