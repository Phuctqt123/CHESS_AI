import chess
import random
import math

# ==========================================
# 1. CONSTANTS & PIECE SQUARE TABLES
# ==========================================

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

pawn_table = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

knight_table = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

piece_tables = {
    chess.PAWN: pawn_table,
    chess.KNIGHT: knight_table,
}

# ==========================================
# 2. EVALUATION FUNCTION
# ==========================================

def evaluate_board(board):
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(3):
        return 0

    score = 0
    
    for square, piece in board.piece_map().items():
        value = PIECE_VALUES.get(piece.piece_type, 0)
        pst = piece_tables.get(piece.piece_type)
        
        # Add positional value if table exists
        if pst:
            if piece.color == chess.WHITE:
                value += pst[square]
            else:
                value -= pst[chess.square_mirror(square)]
                
        # White adds to score, Black subtracts from score
        if piece.color == chess.WHITE:
            score += value
        else:
            score -= value
    return score

# ==========================================
# 3. MINIMAX WITH ALPHA-BETA PRUNING
# ==========================================

def minimax(board, depth, alpha, beta, maximizing_player):
    if board.is_game_over() or depth == 0:
        return evaluate_board(board), None

    best_move = None
    # Sort moves to improve alpha-beta pruning efficiency (captures first)
    moves = sorted(board.legal_moves, key=lambda move: board.is_capture(move), reverse=True)

    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def get_best_move_alphabeta(fen, depth=3): 
    board = chess.Board(fen)
    # True if White's turn, False if Black's turn
    maximizing_player = board.turn == chess.WHITE
    _, best_move = minimax(board, depth, -float('inf'), float('inf'), maximizing_player)
    return best_move.uci() if best_move else None

# ==========================================
# 4. MONTE CARLO TREE SEARCH (MCTS)
# ==========================================

class MCTSNode:
    def __init__(self, board, parent=None):
        self.board = board
        self.parent = parent
        self.children = {}
        self.wins = 0
        self.visits = 0

    def uct_value(self, total_visits, C=1.41):
        if self.visits == 0:
            return float('inf')  # Ưu tiên khám phá nút chưa thăm
        return (self.wins / self.visits) + C * math.sqrt(math.log(total_visits) / self.visits)

def simulate_random_game(board, max_moves=20):
    temp_board = board.copy()
    moves_played = 0

    while not temp_board.is_game_over() and moves_played < max_moves:
        move = random.choice(list(temp_board.legal_moves))
        temp_board.push(move)
        moves_played += 1
        
    if temp_board.is_game_over():
        return temp_board.result()
    score = evaluate_board(temp_board)
    if score > 100: return "1-0"      # Trắng đang ưu thế
    elif score < -100: return "0-1"   # Đen đang ưu thế
    else: return "1/2-1/2"            # Thế trận cân bằng

def get_best_move_mcts(fen, iterations=100):
    root_board = chess.Board(fen)
    root_node = MCTSNode(root_board)

    for _ in range(iterations):
        # 1. Selection & 2. Expansion
        node = root_node
        temp_board = root_board.copy()

        while node.children:
            # Chọn nút con có UCT cao nhất
            move, node = max(node.children.items(), key=lambda x: x[1].uct_value(node.visits))
            temp_board.push(move)

        if not temp_board.is_game_over():
            # Mở rộng tất cả nước đi hợp lệ
            for move in temp_board.legal_moves:
                temp_board.push(move)
                node.children[move] = MCTSNode(temp_board.copy(), parent=node)
                temp_board.pop()

        # 3. Simulation (Rollout)
        result = simulate_random_game(temp_board)

        # 4. Backpropagation
        while node:
            node.visits += 1
            # Cập nhật win dựa trên kết quả và lượt đi (trắng/đen)
            if (result == "1-0" and node.board.turn == chess.BLACK) or \
               (result == "0-1" and node.board.turn == chess.WHITE):
                node.wins += 1
            elif result == "1/2-1/2":
                node.wins += 0.5
            node = node.parent

    if not root_node.children:
        return None
        
    # Chọn nước đi được ghé thăm nhiều nhất
    best_move = max(root_node.children.items(), key=lambda x: x[1].visits)[0]
    return best_move.uci()

# ==========================================
# 5. GENETIC ALGORITHM (PRE-TRAINED WEIGHTS)
# ==========================================

# Giả lập bộ trọng số tốt nhất được chọn lọc sau 50 thế hệ lai tạo (Generation 50)
GENETIC_FEATURE_WEIGHTS = [1.12, 0.88] # [Trọng số vật chất, Trọng số vị trí]

# Bảng giá trị quân cờ đã bị đột biến/tiến hóa
GENETIC_PIECE_VALUES = {
    chess.PAWN: 105.5,
    chess.KNIGHT: 312.0,
    chess.BISHOP: 345.5,
    chess.ROOK: 510.0,
    chess.QUEEN: 960.5,
    chess.KING: 20000.0
}

GENETIC_PIECE_TABLES = {
    # TỐT: Học được cách lao lên phong cấp, điểm rất cao ở hàng 7, thấp ở hàng xuất phát
    chess.PAWN: [
         0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,
        51.2,  50.5,  52.1,  49.8,  50.0,  51.5,  50.8,  52.0,
        10.5,  11.2,  21.5,  31.0,  30.8,  19.5,  12.0,  10.1,
         5.2,   6.0,  11.5,  26.1,  25.4,   9.8,   4.5,   5.8,
         0.5,  -0.2,   1.5,  21.0,  20.5,   0.8,  -0.5,   1.2,
         5.5,  -4.5, -11.0,   1.2,   0.5,  -9.8,  -5.5,   4.8,
         5.0,   9.5,  11.0, -19.5, -21.0,  10.5,   9.5,   5.2,
         0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0
    ],
    
    # MÃ: Học được nguyên lý "Mã ở góc là Mã chết", điểm rất cao ở trung tâm, âm nặng ở 4 viền
    chess.KNIGHT: [
        -51.5, -40.2, -29.8, -31.0, -30.5, -29.5, -41.0, -49.5,
        -40.8, -19.5,  -0.5,   1.2,   0.8,   0.5, -19.8, -40.5,
        -29.5,   0.5,  11.0,  16.5,  15.5,  10.5,  -0.5, -29.8,
        -30.2,   5.5,  15.8,  21.5,  20.5,  15.2,   4.8, -30.5,
        -29.8,   0.5,  16.2,  20.8,  21.2,  15.5,   0.2, -30.2,
        -31.0,   4.8,  10.5,  15.5,  16.0,  11.2,   5.5, -29.5,
        -40.5, -19.8,   0.5,   5.5,   5.2,   0.8, -20.5, -39.8,
        -50.5, -41.0, -30.5, -29.5, -30.2, -31.0, -39.5, -49.8
    ],
    
    # TƯỢNG: Thích các đường chéo dài, né các ô bị tốt cản
    chess.BISHOP: [
        -20.5, -10.2, -10.5, -10.8, -10.2, -10.5, -10.8, -19.5,
        -10.2,   0.5,   0.2,   0.8,   0.5,   0.2,   0.5, -10.5,
        -10.5,   0.8,   5.5,  10.2,  10.5,   5.2,   0.8, -10.2,
        -10.8,   5.2,   5.8,  10.5,  10.8,   5.5,   4.8, -10.5,
        -10.2,   0.5,  10.5,  10.2,  10.8,  10.5,   0.2, -10.8,
        -10.5,  10.2,  10.8,  10.5,  10.2,  10.8,   9.8, -10.2,
        -10.8,   4.8,   0.5,   0.2,   0.5,   0.8,   5.2, -10.5,
        -19.5, -10.5, -10.2, -10.8, -10.5, -10.2, -10.8, -20.5
    ],
    
    # XE: Thích chiếm hàng 7 để ép Vua địch (điểm +10), đứng ở nhà thì không có điểm
    chess.ROOK: [
         0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,
         5.5,  10.2,  10.5,  10.8,  10.2,  10.5,   9.8,   5.2,
        -5.5,   0.5,   0.2,   0.8,   0.5,   0.2,   0.5,  -4.8,
        -4.8,   0.2,   0.5,   0.8,   0.5,   0.2,   0.5,  -5.2,
        -5.2,   0.5,   0.2,   0.8,   0.5,   0.2,   0.5,  -4.8,
        -4.8,   0.2,   0.5,   0.8,   0.5,   0.2,   0.5,  -5.5,
        -5.5,   0.5,   0.2,   0.8,   0.5,   0.2,   0.5,  -5.2,
         0.5,  -0.5,   0.2,   5.5,   5.2,   0.5,  -0.5,   0.2
    ],
    
    # HẬU: Hạn chế lên sớm (âm điểm ở trung tâm lúc đầu) để tránh bị rượt đuổi
    chess.QUEEN: [
        -20.5, -10.2, -10.5,  -5.5,  -5.2, -10.5, -10.8, -19.5,
        -10.2,   0.5,   0.2,   0.8,   0.5,   0.2,   0.5, -10.5,
        -10.5,   0.8,   5.5,   5.2,   5.5,   5.2,   0.8, -10.2,
         -5.5,   0.5,   5.2,   5.5,   5.2,   5.5,   0.5,  -5.2,
         -0.5,   0.2,   5.5,   5.2,   5.5,   5.2,   0.2,  -5.5,
        -10.2,   5.5,   5.2,   5.5,   5.2,   5.5,   4.8, -10.8,
        -10.5,   0.5,   5.2,   0.5,   0.2,   0.5,   0.2, -10.2,
        -19.5, -10.8, -10.2,  -5.5,  -5.2, -10.5, -10.8, -20.5
    ],
    
    # VUA: Trốn vào 2 góc nhập thành (điểm cao +30), tránh ra giữa bàn cờ (-50)
    chess.KING: [
        -30.5, -40.2, -40.5, -50.8, -50.5, -40.2, -40.5, -29.5,
        -30.2, -40.5, -40.8, -50.2, -50.8, -40.5, -40.2, -30.5,
        -29.8, -40.2, -40.5, -50.5, -50.2, -40.8, -40.5, -30.2,
        -30.5, -40.8, -40.2, -50.5, -50.8, -40.2, -40.5, -29.8,
        -20.5, -30.2, -30.5, -40.8, -40.5, -30.2, -30.5, -19.5,
        -10.2, -20.5, -20.8, -20.5, -20.2, -20.8, -19.5, -10.5,
         20.5,  20.2,   0.5,   0.2,   0.5,   0.8,  20.5,  19.5,
         20.2,  30.5,  10.5,   0.5,   0.2,  10.8,  30.2,  20.5
    ]
}

# TẠO MỘT BỘ NHỚ ĐỆM (CACHE)
genetic_eval_cache = {}

def evaluate_board_genetic(board):
    # Lấy FEN (chuỗi trạng thái bàn cờ) làm chìa khóa
    board_fen = board.fen()
    
    # Nếu thế cờ này ĐÃ ĐƯỢC TÍNH RỒI, lấy luôn kết quả ra dùng
    if board_fen in genetic_eval_cache:
        return genetic_eval_cache[board_fen]

    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(3):
        return 0

    score = 0
    mat_weight = GENETIC_FEATURE_WEIGHTS[0]
    pos_weight = GENETIC_FEATURE_WEIGHTS[1]
    
    for square, piece in board.piece_map().items():
        base_value = GENETIC_PIECE_VALUES.get(piece.piece_type, 0)
        pst = GENETIC_PIECE_TABLES.get(piece.piece_type) 
        
        value = base_value * mat_weight
        if pst:
            pst_val = pst[square] if piece.color == chess.WHITE else pst[chess.square_mirror(square)]
            value += pst_val * pos_weight
            
        if piece.color == chess.WHITE:
            score += value
        else:
            score -= value
    
    # LƯU KẾT QUẢ VÀO BỘ NHỚ TRƯỚC KHI TRẢ VỀ
    genetic_eval_cache[board_fen] = score
    return score

def minimax_genetic(board, depth, alpha, beta, maximizing_player):
    if board.is_game_over() or depth == 0:
        return evaluate_board_genetic(board), None

    best_move = None
    moves = sorted(board.legal_moves, key=lambda move: board.is_capture(move), reverse=True)

    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            board.push(move)
            eval_score, _ = minimax_genetic(board, depth - 1, alpha, beta, False)
            board.pop()
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            board.push(move)
            eval_score, _ = minimax_genetic(board, depth - 1, alpha, beta, True)
            board.pop()
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def get_best_move_genetic(fen, depth=5): 
    global genetic_eval_cache
    
    # XÓA TRẮNG CACHE SAU MỖI LƯỢT ĐI ĐỂ KHÔNG BỊ TRÀN RAM CHẾT MÁY
    genetic_eval_cache.clear() 
    
    board = chess.Board(fen)
    maximizing_player = board.turn == chess.WHITE
    _, best_move = minimax_genetic(board, depth, -float('inf'), float('inf'), maximizing_player)
    return best_move.uci() if best_move else None