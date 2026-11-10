from flask import Flask, request
from queue import Queue

event_queue = Queue()

app = Flask(__name__)

@app.route('/event', methods=['POST'])
def receive_event():
    data = request.json
    if not data:
        return {"error": "No data received"}, 400
    event_queue.put(data)
    return {"status": "Event received"}, 200

def run_server():
    app.run(port=5000, debug=False, use_reloader=False)

