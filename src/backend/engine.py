import chess
import random
import math

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


def get_best_move(fen, iterations=800):
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

    # Chọn nước đi được ghé thăm nhiều nhất
    best_move = max(root_node.children.items(), key=lambda x: x[1].visits)[0]
    return best_move.uci()


def simulate_random_game(board):
    temp_board = board.copy()
    while not temp_board.is_game_over():
        move = random.choice(list(temp_board.legal_moves))
        temp_board.push(move)
    return temp_board.result()