from flask import Flask, jsonify
from flask_cors import CORS
from optimize import get_irrigation_decision

app = Flask(__name__)
CORS(app)

@app.route("/api/irrigation", methods=["GET"])
def irrigation_data():
    data = get_irrigation_decision()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
