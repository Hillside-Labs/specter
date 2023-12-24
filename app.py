from main import main
from flask import *
from wtforms import *
from wtforms.validators import AnyOf

app = Flask(__name__)

class AnalysisForm(Form):
    data_format = StringField("Format", [AnyOf(["json", "yaml"])])
    spec_url = URLField("Spec URL", [validators.URL()])
    audience = StringField("Audience")
    use_cases = StringField("Use-cases")
    comments = StringField("Comments")

@app.route("/", methods=["POST", "GET"])
def index():
    form = AnalysisForm(request.form)

    if request.method == "GET":
        return render_template("index.html")

    elif request.method == "POST" and form.validate():
        return render_template(
            "answers.html",
            query_answers=main(
                form.data_format.data,
                form.spec_url.data,
                form.audience.data,
                form.use_cases.data,
                form.comments.data,
            ),
        )
# todo: deploy to fly