from flask import Flask, render_template, request
import math

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    if request.method == "POST":
        expression = request.form["expression"]

        try:
            # Replace scientific functions
            expression = expression.replace("sin", "math.sin")
            expression = expression.replace("cos", "math.cos")
            expression = expression.replace("tan", "math.tan")
            expression = expression.replace("sqrt", "math.sqrt")
            expression = expression.replace("log", "math.log10")
            expression = expression.replace("pi", "math.pi")
            expression = expression.replace("e", "math.e")

            result = eval(expression)
        except:
            result = "Error"

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
