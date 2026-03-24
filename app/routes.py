from flask import jsonify
from app import app, mongo

@app.route("/")
def home():
    return jsonify({"status": "success", "message": "App is running"})

@app.route("/webinars", methods=["GET"])
def get_webinars():
    try:
        webinars = list(mongo.db.webinar_data.find({}, {"_id": 0}))
        return jsonify({
            "status": "success",
            "count": len(webinars),
            "data": webinars
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
