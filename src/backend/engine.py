import chess
import random
import math

# ==========================================
# 1. ALPHA-BETA ENGINE
# ==========================================
eval_cache = {}
tt_cache = {}

piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

piece_square_tables = {
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

def evaluate_king_safety(board: chess.Board) -> float:
    safety = 0.0
    for color in (chess.WHITE, chess.BLACK):
        king_square = board.king(color)
        sign = 1 if color == chess.WHITE else -1
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        shield_files = [f for f in (king_file-1, king_file, king_file+1) if 0 <= f <= 7]

        for f in shield_files:
            rank_in_front_of_king = king_rank + sign
            if 0 <= rank_in_front_of_king <= 7:
                sq = chess.square(f, rank_in_front_of_king)
                p = board.piece_at(sq)
                if p and p.piece_type == chess.PAWN and p.color == color:
                    safety += sign * 30
    return safety

def eval_board(board: chess.Board):
    key = board.board_fen
    if key in eval_cache:
        return eval_cache[key]

    if board.is_checkmate():
        res = board.result()
        if res == '1-0': return float('inf')
        elif res == '0-1' : return float('-inf')

    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(3):
        return 0.0

    score = 0
    mat_weight = 1.0
    piece_position_weight = 1.0
    piece_mobility_weight = 1.0
    king_safety_weight = 1.0

    for square, piece in board.piece_map().items():
        sign = 1 if piece.color == chess.WHITE else -1
        base_piece_value = piece_values[piece.piece_type]
        pst = piece_square_tables[piece.piece_type]
        sq = square if piece.color == chess.WHITE else chess.square_mirror(square)

        piece_value = base_piece_value * mat_weight + pst[sq] * piece_position_weight
        score += sign * piece_value

        piece_mobility = len(board.attacks(square))
        score += sign * piece_mobility_weight * piece_mobility

    king_safety = evaluate_king_safety(board)
    score += king_safety_weight * king_safety

    eval_cache[key] = score
    return score

def order_moves(board):
    moves = list(board.legal_moves)
    def move_score(move):
        board.push(move)
        key = board._transposition_key()
        score = eval_cache.get(key, eval_board(board))
        board.pop()
        return score
    return sorted(moves, key=move_score, reverse=(board.turn == chess.WHITE))

def minimax(board: chess.Board, depth, alpha=float('-inf'), beta=float('inf')):
    key = (board.fen(), depth)
    if key in tt_cache: return tt_cache[key]
    if depth == 0 or board.is_game_over(): return eval_board(board)

    if board.turn == chess.WHITE:
        value = float('-inf')
        for move in order_moves(board):
            board.push(move)
            value = max(value, minimax(board, depth - 1, alpha, beta))
            board.pop()
            alpha = max(alpha, value)
            if alpha >= beta: break
        tt_cache[key] = value
        return value
    else:
        value = float('inf')
        for move in order_moves(board):
            board.push(move)
            value = min(value, minimax(board, depth - 1, alpha, beta))
            board.pop()
            beta = min(beta, value)
            if beta <= alpha: break
        tt_cache[key] = value
        return value

def get_best_move_alphabeta(fen, depth=3):
    board = chess.Board(fen)
    is_max = board.turn == chess.WHITE
    best_moves = []
    best_score = float('-inf') if is_max else float('inf')
    alpha, beta = float('-inf'), float('inf')

    for move in order_moves(board):
        board.push(move)
        score = minimax(board, depth - 1, alpha, beta)
        board.pop()
        if is_max:
            if score > best_score:
                best_score = score
                best_moves = [move]
                alpha = score
            elif score == best_score:
                best_moves.append(move)
        else:
            if score < best_score:
                best_score = score
                best_moves = [move]
                beta = score
            elif score == best_score:
                best_moves.append(move)
            if beta <= alpha: break
    
    if not best_moves: return None
    return random.choice(best_moves).uci()


# ==========================================
# 2. MONTE CARLO TREE SEARCH (Pure MCTS)
# ==========================================
class MCTSNode:
    def __init__(self, board, parent=None):
        self.board = board
        self.parent = parent
        self.children = {}
        self.wins = 0
        self.visits = 0

    def uct_value(self, total_visits, C=1.41):
        if self.visits == 0: return float('inf')  
        return (self.wins / self.visits) + C * math.sqrt(math.log(total_visits) / self.visits)

def simulate_random_game(board):
    temp_board = board.copy()
    limit = 50  # Giới hạn số nước đi ngẫu nhiên để tránh mô phỏng chạy quá lâu
    while not temp_board.is_game_over() and limit > 0:
        # Bốc ngẫu nhiên hoàn toàn 100% đúng chuẩn MCTS thuần túy
        move = random.choice(list(temp_board.legal_moves))
        temp_board.push(move)
        limit -= 1
    
    res = temp_board.result()
    if res == '*': 
        # Nếu chưa phân thắng bại sau limit nước đi, coi như hòa
        return '1/2-1/2'
    return res

def get_best_move_mcts(fen, iterations=50):
    root_board = chess.Board(fen)
    root_node = MCTSNode(root_board)
    for _ in range(iterations):
        node, temp_board = root_node, root_board.copy()
        
        # 1. Selection
        while node.children:
            move, node = max(node.children.items(), key=lambda x: x[1].uct_value(node.visits))
            temp_board.push(move)
            
        # 2. Expansion
        if not temp_board.is_game_over():
            for move in temp_board.legal_moves:
                temp_board.push(move)
                new_node = MCTSNode(temp_board.copy(), parent=node)
                # XÓA LAI TẠP: Không dùng eval_board() nữa, node mới bắt đầu từ 0
                node.children[move] = new_node
                temp_board.pop()
                
        # 3. Simulation (Rollout thuần ngẫu nhiên)
        result = simulate_random_game(temp_board)
        
        # 4. Backpropagation
        while node:
            node.visits += 1
            if (result == "1-0" and node.board.turn == chess.BLACK) or \
               (result == "0-1" and node.board.turn == chess.WHITE): node.wins += 1
            elif result == "1/2-1/2": node.wins += 0.5
            node = node.parent
            
    if not root_node.children: return None
    return max(root_node.children.items(), key=lambda x: x[1].visits)[0].uci()


# ==========================================
# 3. GENETIC ALGORITHM (Evolutionary Weights)
# ==========================================

GENETIC_FEATURE_WEIGHTS = [1.12, 0.88] 

GENETIC_PIECE_VALUES = {
    chess.PAWN: 105.5,
    chess.KNIGHT: 312.0,
    chess.BISHOP: 345.5,
    chess.ROOK: 510.0,
    chess.QUEEN: 960.5,
    chess.KING: 20000.0
}

GENETIC_PIECE_TABLES = {
    chess.PAWN: [
        -37.451509842498034, 89.7767296388379, 50.24716370179206, 14.097250470483232, 72.21564311459451, -55.10530813105872, -73.2682545654271, -16.12279694128364,
        -85.27738487979215, 79.71733193884046, -4.489292992546234, -38.077616586627585, -83.82725735328627, -90.55308481582404, 68.86915019611078, -31.832832845543834,
        -39.022064733662994, 11.805736584271216, -51.158457324260894, 98.69598179686767, 38.958334338248164, -8.617713418398836, 10.996493732956282, -54.8281190841412,
        36.32741457624172, -17.36705363627607, -50.026675002292805, -55.96419479428374, 36.36409085046185, 97.0623958851015, -39.08007379832803, 15.247517556060156,
        88.21072513641002, -41.88720376095265, 97.97066447346438, -87.06104172002303, -97.10884612465316, 7.169579144163805, -31.57375252544641, 15.964010071046236,
        100.33077379347286, -85.04473197578403, -1.6709752781017917, -48.4225945032388, 85.10656709745824, 28.069848382516028, 60.16494643322482, 72.06823196468767,
        -26.721466073540796, -14.770029976115111, 52.18619663266077, 1.0640519007248912, -88.06526804658303, 40.34755781930778, 50.523633507217426, 34.89409642124147,
        9.223764826200082, -93.84772378589771, 66.19327546485736, -95.16166940929185, -77.4898700698428, -55.79177971334589, 92.83939401048659, -91.49067549355014
    ],
    chess.KNIGHT: [
        -24.58653865886152, -96.9073966452871, -16.106480701379567, -79.24845693073601, -90.13093085130588, 42.00367512117334, -80.69748749838175, 10.050959418404787,
        -61.34735169005092, -78.87288740251749, 79.99670999374163, -79.52110595880728, 61.192047884634974, 89.91301178469115, -72.26792607803148, -3.1366292665648388,
        -50.88972012888066, -41.34637601725759, -75.020036697792, 29.317266211368253, -83.50321517683068, -65.71679043335368, 52.13060709369856, -51.47670606150425,
        35.55667983485682, 92.8224892872372, 31.841063647297517, -98.16868724586001, -44.872080750669575, 17.769756249311385, 3.2397664822263863, 64.18915593987501,
        72.56941337691534, 62.94654087622999, 22.521675249309766, 99.91476497699173, 48.94777367575202, 4.605745045042141, -67.42636429220283, -16.173952541015325,
        -19.834548057591903, -25.707622643570282, -72.7474469737593, 68.69091530482419, 53.2333389373523, 26.95425762227117, 33.57232276688521, 88.23063617584208,
        67.33780520787495, -83.98568010043606, -35.895298796724944, 50.01044106693024, -76.75411183720189, 36.03070093904918, 25.651565255223915, -84.02088887674813,
        75.763070119995, -29.2178636891624, 24.53030948622488, 20.235257747520023, 27.3709849767127, -99.66064048851602, -75.2061358351521, -0.23799694267474703
    ],
    chess.BISHOP: [
        68.63818736475363, -52.1197584400945, -18.70748785367269, -92.24965159263763, -56.33588957001781, -10.89473333789033, 86.96194943375315, -57.44489801991948,
        17.057534757762767, -17.60612558282439, -63.01003048929128, -76.77599898110516, 59.45319768146092, 42.655457332633944, 52.723175455952486, -31.920018636532603,
        53.676887594053696, -5.347270449273328, 97.9700563152, 37.992213019138944, -78.66828622221433, 45.91625129049248, -3.556456891534613, -81.0397846375641,
        -91.65617646353523, -44.90740902823702, -8.358112765447352, -54.01206344382157, 9.05793658014224, 61.28114112377584, 68.9903594040953, 17.86574669499919,
        -39.859424189001146, 53.65831031699349, 93.08384578098088, -40.871463204164286, -14.136792030313487, 75.33937098971998, 45.51313817070775, -57.0875616909549,
        2.5835658709819427, -16.655684798660616, 92.20189760763009, 36.922568896955795, 59.049870010314805, -54.91575408172843, 21.624253418164102, 76.4467090544868,
        -19.734103989573562, 60.89821377132431, -43.833014197809625, 28.40458130444304, -78.15445508569239, 83.62744941910154, -81.16175350841078, 46.9395085815445,
        -23.106014011192272, 73.9356846870928, 82.48036895698486, 91.89553594671935, -42.32903533713763, -6.559658127379201, 36.520577089252924, -95.30612291834821
    ],
    chess.ROOK: [
        30.884151946154503, -80.07800512517653, -11.64352722735202, -77.9173867915919, 59.93095286481261, 9.440460209025645, 31.104248123647807, 22.313167329394943,
        -96.61349248867926, 33.68613831552034, 90.99255048503619, -81.40936319996632, 20.099452752478044, 24.698612831638215, 61.73698839998714, -97.27392321865437,
        68.19876283643157, 26.3526327726857, 83.67535581308451, 73.42393408368021, 36.26742901540209, -41.31623403009239, -38.78769646754865, 80.2737651488284,
        10.9908198157982, 89.67213274235294, -53.528375876715906, 50.48770647393919, 83.44177040797982, -9.411350064580049, 65.28468576520011, -63.92756031137,
        -52.36885800664852, 38.13475619580663, -64.47737611546563, 13.4085979852835, -84.66703510693314, 78.96096212075506, 55.77941234962914, -21.4834404019649,
        -28.348565084516267, -10.503444520018974, -93.29269167417937, -41.57704855092843, 63.040693951328784, 71.93954560107773, -83.20075563781086, -2.7959763753216267,
        95.40455132943498, -63.491305642162274, 3.665323135084691, -86.20830881746993, 50.23517857578541, -34.977835860997786, 84.59196800753648, 23.64595522453594,
        -33.35969799833573, 36.40510505141762, 99.98138175016337, 48.69797721207874, -58.570179988228155, -18.62714246835708, -28.626609962483258, -70.7302222991961
    ],
    chess.QUEEN: [
        -70.45526724401475, 95.32283319349878, -45.226279853550324, -51.61784635209254, -68.92542478228606, -88.23803677170415, -26.859807275279366, 92.76778386790795,
        -4.9687122992346815, -73.37688555748947, 13.525683516915942, -65.7199986633824, 66.50927654974129, -47.151231696091216, -27.815290187586395, 92.22677147907962,
        2.5359816975877516, 29.983377815420596, 17.79993561390023, 74.59435520838161, 65.63228275746503, 17.082416413533494, -24.796811402211247, 95.52590100214357,
        58.89834510775472, -61.692508127414456, 41.318738042182005, 88.75272972903159, -29.678714117961164, 54.69875846960798, -97.65058576901366, 69.73920996294777,
        31.498502072163927, -30.63699480074449, 11.39023715439032, 62.34960609021991, 61.62280279269087, -45.082305537430244, 19.584067179519046, -21.83210107161912,
        26.123556198355843, -29.298735548665306, 32.933396927416936, 61.28808367033403, -2.270026332799733, 35.52646965742176, -31.880339537654436, 13.552523619439611,
        -76.00410012209069, 80.65346313149936, 96.83896031397663, -35.87948782727079, -62.047672558739905, 88.25871511697648, 27.10666865888183, -8.286661306258878,
        46.24777479013204, -19.755259585115123, -2.379705007021144, -59.039749990678956, 13.418678892795157, -8.89425372640838, -53.49132875440588, 63.7088493799923
    ],
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

genetic_eval_cache = {}

def evaluate_board_genetic(board):
    board_fen = board.fen()
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
    genetic_eval_cache.clear() 
    
    board = chess.Board(fen)
    maximizing_player = board.turn == chess.WHITE
    _, best_move = minimax_genetic(board, depth, -float('inf'), float('inf'), maximizing_player)
    return best_move.uci() if best_move else None