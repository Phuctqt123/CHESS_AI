import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import webbrowser
import chess
import webbrowser
import threading

# Gọi đủ cả 3 thuật toán từ engine
from .engine import get_best_move_alphabeta, get_best_move_mcts, get_best_move_genetic

# Cấu hình đường dẫn thư mục static và template
base_dir = os.path.dirname(os.path.abspath(__file__))
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
    
    # Nhận algo và depth từ 2 thanh trượt của Frontend
    algo = data.get('algo', 'alphabeta')
    depth = int(data.get('depth', 3))

    # Điều phối logic dựa trên tùy chọn của người dùng
    if algo == 'mcts':
        # UI hiển thị iterations = depth * 100, nên ta truyền thẳng vào đây
        move = get_best_move_mcts(fen, iterations=depth * 50)
    elif algo == 'genetic':
        move = get_best_move_genetic(fen, depth=depth)
    else: 
        # Mặc định là alphabeta
        move = get_best_move_alphabeta(fen, depth=depth)

    return jsonify({"move": move})

def open_browser():
    if os.environ.get('Open_Browser', 'True') == 'True':
        webbrowser.open(f"http://127.0.0.1:{os.environ.get('PORT', 5003)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)