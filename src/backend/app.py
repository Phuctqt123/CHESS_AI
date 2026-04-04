import os
from flask import Flask, request, jsonify, render_template
import chess
import random
from flask_cors import CORS
import webbrowser
import threading
from .engine import get_best_move

# Configure absolute paths for static and template folders
base_dir = os.path.dirname(os.path.abspath(__file__))
# Base dir is /src/backend
# Templates is /src/frontend/templates
# Static is /src/frontend/static
template_dir = os.path.join(base_dir, '..', 'frontend', 'templates')
static_dir = os.path.join(base_dir, '..', 'frontend', 'static')

app = Flask(__name__, 
            template_folder=template_dir, 
            static_folder=static_dir,
            static_url_path='/static')
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/move', methods=['POST'])
def get_move():
    data = request.get_json()
    fen = data.get('fen')
    mode = data.get('algo', 'alpha_beta')

    val = int(data.get('value', 3))

    if mode == "mcts":
        move = get_best_move(fen, mode="mcts", iterations=val * 100)
    else:
        move = get_best_move(fen, mode="alpha_beta", depth=val)

    return jsonify({"move": move})


def open_browser():
    # Only open browser if not in a container and matching env
    if os.environ.get('Open_Browser', 'True') == 'True':
        webbrowser.open(f"http://127.0.0.1:{os.environ.get('PORT', 5003)}")