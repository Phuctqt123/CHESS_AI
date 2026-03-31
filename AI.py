import chess
import random


piece_value = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0, # ai cũng có vua nên ta ko quan tâm lắm
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

class Agent:
    def __init__(self,
        mobility_weight: float = 1.0,
        material_weight: float = 1.0,
        activity_weight: float = 1.0,
    ):
        self.mobility_weight = mobility_weight
        self.material_weight = material_weight
        self.activity_weight = activity_weight


def eval(board: chess.Board, agent: Agent):
    sign = 1 if board.turn == chess.WHITE else -1 # true for white's turn, false for black's turn
    if (board.is_checkmate()):
        return sign * inf

    can_draw_by_game_rule = board.is_stalemate() or \
        board.is_insufficient_material() or \
        board.is_fivefold_repetition() or \
        board.is_seventyfive_moves() or \
        board.can_claim_draw()

    if can_draw_by_game_rule:
        return 0

    score = 0

    board.turn = chess.WHITE
    white_legal_moves_count = board.legal_moves.count()
    board.turn = chess.BLACK
    black_legal_moves_count = board.legal_moves.count()
    board.turn = chess.WHITE if sign == 1 else chess.BLACK
    score += agent.mobility_weight * (white_legal_moves_count - black_legal_moves_count)

    white_material = 0
    black_material = 0
    activity = 0
    for square, piece in board.piece_map().items():
        value = piece_value[piece.piece_type]

        pst = piece_tables.get(piece.piece_type)
        if pst:
            if piece.color == chess.WHITE:
                value += pst[square]
            else:
                value -= pst[chess.square_mirror(square)]

        if piece.color == chess.WHITE:
            white_material += value
            activity += len(board.attacks(square))
        else:
            black_material += value
            activity -= len(board.attacks(square))

    score += agent.material_weight * (white_material - black_material)
    score += agent.activity_weight * activity

    center = [chess.D4, chess.E4, chess.D5, chess.E5]
    for sq in center:
        piece = board.piece_at(sq)
        if piece:
            score += 10 if piece.color == chess.WHITE else -10

    if board.is_check():
        score -= 50 if board.turn == chess.WHITE else -50

    return score


def get_best_move(fen):
    """
    INPUT:
        fen (str): Chuỗi FEN mô tả trạng thái bàn cờ hiện tại
                   Ví dụ:
                   "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    OUTPUT:
        str: nước đi ở dạng UCI (Universal Chess Interface)
             ví dụ: "e2e4", "g1f3", ...
        hoặc:
        None: nếu không còn nước đi hợp lệ (checkmate / stalemate)
    """

    # Tạo bàn cờ từ FEN
    board = chess.Board(fen)

    # Lấy danh sách tất cả nước đi hợp lệ
    moves = list(board.legal_moves)

    # Nếu không còn nước đi → kết thúc ván
    if not moves:
        return None

    # Chọn ngẫu nhiên 1 nước đi
    move = random.choice(moves)

    # Trả về dạng UCI (ví dụ: e2e4)
    return move.uci()
