import random
import copy
import chess
import pickle
import os
import signal
import time
from multiprocessing import Pool, cpu_count

# Bộ nhớ đệm toàn cục để tăng tốc tìm kiếm nước đi hợp lệ
legal_moves_cache = {}

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

class Agent:
    def __init__(self):
        self.rating: float = 1000.0
        self.n_features = 2
        self.feature_weights: list[float] = []
        self.piece_values: dict[int, float] = {
            chess.PAWN: 0.0, chess.KNIGHT: 0.0, chess.BISHOP: 0.0,
            chess.ROOK: 0.0, chess.QUEEN: 0.0, chess.KING: 0.0
        }
        self.piece_tables = {
            chess.PAWN: [], chess.KNIGHT: [], chess.BISHOP: [],
            chess.ROOK: [], chess.QUEEN: [], chess.KING: []
        }
        self.__eval_cache = {}
        self.__tt_cache = {}
        self.__randomize_values()

    def __randomize_values(self):
        self.feature_weights = [random.uniform(0.0, 2.0), random.uniform(0.0, 2.0)]
        self.piece_values = {
            chess.PAWN: random.uniform(0, 200),
            chess.KNIGHT: random.uniform(0, 500),
            chess.BISHOP: random.uniform(0, 500),
            chess.ROOK: random.uniform(0, 800),
            chess.QUEEN: random.uniform(0, 1200),
            chess.KING: 0
        }
        for piece_type in self.piece_tables:
            self.piece_tables[piece_type] = [random.uniform(-100, 100) for _ in range(64)]

    def eval_board(self, board: chess.Board):
        key = board.board_fen
        if key in self.__eval_cache: return self.__eval_cache[key]
        if board.is_checkmate():
            res = board.result()
            return float('inf') if res == '1-0' else float('-inf')
        if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(3):
            return 0.0

        score = 0
        mat_w, pos_w = self.feature_weights
        for square, piece in board.piece_map().items():
            base_val = self.piece_values[piece.piece_type]
            pst = self.piece_tables[piece.piece_type]
            sq = square if piece.color == chess.WHITE else chess.square_mirror(square)
            val = base_val * mat_w + pst[sq] * pos_w
            score += val if piece.color == chess.WHITE else -val
        self.__eval_cache[key] = score
        return score

    def clearEvalCache(self):
        self.__eval_cache.clear()
        self.__tt_cache.clear()

    def __order_moves(self, board):
        moves = list(board.legal_moves)
        def move_score(move):
            board.push(move)
            key = board._transposition_key()
            score = self.__eval_cache.get(key, 0.0)
            board.pop()
            return score
        return sorted(moves, key=move_score, reverse=(board.turn == chess.WHITE))

    def __minimax(self, board: chess.Board, depth, alpha=float('-inf'), beta=float('inf')):
        key = (board.fen(), depth)
        if key in self.__tt_cache: return self.__tt_cache[key]
        if depth == 0 or board.is_game_over():
            score = self.eval_board(board)
            self.__tt_cache[key] = score
            return score

        if board.turn == chess.WHITE:
            value = float('-inf')
            for move in self.__order_moves(board):
                board.push(move)
                value = max(value, self.__minimax(board, depth - 1, alpha, beta))
                board.pop()
                alpha = max(alpha, value)
                if alpha >= beta: break
            self.__tt_cache[key] = value
            return value
        else:
            value = float('inf')
            for move in self.__order_moves(board):
                board.push(move)
                value = min(value, self.__minimax(board, depth - 1, alpha, beta))
                board.pop()
                beta = min(beta, value)
                if beta <= alpha: break
            self.__tt_cache[key] = value
            return value

    def evaluate_move(self, args):
        fen, move_uci, depth = args
        board = chess.Board(fen)
        board.push(chess.Move.from_uci(move_uci))
        score = self.__minimax(board, depth - 1)
        return move_uci, score

    def get_best_moves(self, board: chess.Board, depth: int = 3):
        moves = list(board.legal_moves)
        if not moves: return []
        results = []
        fen = board.fen()
        for move in moves:
            results.append(self.evaluate_move((fen, move.uci(), depth)))
        
        move_scores = {chess.Move.from_uci(m): s for m, s in results}
        best_score = max(move_scores.values()) if board.turn == chess.WHITE else min(move_scores.values())
        return [m for m, s in move_scores.items() if s == best_score]

    def get_move(self, board: chess.Board, depth: int = 3):
        best_moves = self.get_best_moves(board, depth)
        return random.choice(best_moves) if best_moves else None

def play_game(agent1: Agent, agent2: Agent, max_n_moves: int = 50, depth: int = 3):
    board = chess.Board()
    for _ in range(max_n_moves * 2):
        if board.is_game_over():
            res = board.result()
            if res == '1-0': return 1.0
            if res == '0-1': return -1.0
            return 0.5
        move = agent1.get_move(board, depth) if board.turn == chess.WHITE else agent2.get_move(board, depth)
        if move is None: break
        board.push(move)
    return 0.0

def update_elo(r_a, r_b, game_res):
    if abs(game_res) < 1e-10: return r_a
    expected = 1 / (1 + 10 ** ((r_b - r_a)/400))
    score = game_res + 1.0 if game_res < 0.0 else game_res
    k = 40 if r_a < 1700 else (10 if r_a > 2400 else 20)
    return r_a + k * (score - expected)

def play_match(args):
    i, j, a, b = args
    result = play_game(a, b)
    return (i, update_elo(a.rating, b.rating, result) - a.rating, j, update_elo(b.rating, a.rating, -result) - b.rating)

def evaluate_population(population: list[Agent], games_per_agent=5):
    indices = list(range(len(population)))
    matchups = []
    for i in indices:
        opps = random.sample(indices, games_per_agent)
        while i in opps: opps = random.sample(indices, games_per_agent)
        for j in opps: matchups.append((i, j, population[i], population[j]))

    pool = Pool(processes=cpu_count()-1, initializer=init_worker)
    try:
        print(f"  Fighting: {len(matchups)} parallel matches...")
        result_async = pool.map_async(play_match, matchups)
        
        while not result_async.ready():
            time.sleep(1) 
            
        results = result_async.get()
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C detected! Terminating all workers immediately...")
        pool.terminate()
        pool.join()
        raise
    finally:
        pool.close()
        pool.join()

    deltas = [0.0 for _ in population]
    for i, d_i, j, d_j in results:
        deltas[i] += d_i
        deltas[j] += d_j

    ratings = {}
    for i, agent in enumerate(population):
        agent.rating += deltas[i]
        ratings[agent] = agent.rating
    return ratings

def select(population, fitnesses, top_k=3):
    paired = sorted([(a, fitnesses[a]) for a in population], key=lambda x: x[1], reverse=True)
    return [a for a, _ in paired[:top_k]]

def crossover(p1, p2):
    child = copy.deepcopy(p1)
    child.clearEvalCache()
    if random.random() < 0.5: child.feature_weights = p2.feature_weights
    for p in child.piece_values:
        if random.random() < 0.5: child.piece_values[p] = p2.piece_values[p]
    for p in child.piece_tables:
        for idx in range(64):
            if random.random() < 0.5: child.piece_tables[p][idx] = p2.piece_tables[p][idx]
    return child

def mutate(agent, rate=0.1):
    for i in range(len(agent.feature_weights)):
        if random.random() < rate: agent.feature_weights[i] += random.uniform(-0.2, 0.2)
    for p in agent.piece_values:
        if random.random() < rate: agent.piece_values[p] += random.uniform(-20, 20)
    return agent

def save_checkpoint(pop, gen, filename="ga_checkpoint.pkl"):
    print(f"  Saving Gen {gen}...")
    with open(filename, "wb") as f:
        pickle.dump({"generation": gen, "population": pop}, f)

def load_checkpoint(filename="ga_checkpoint.pkl"):
    if not os.path.exists(filename): return None, 0
    print(f"  Loading {filename}...")
    with open(filename, "rb") as f:
        data = pickle.load(f)
    return data["population"], data["generation"]

def run_ga(pop_size=10, generations=100):
    checkpoint_file = "ga_checkpoint.pkl"
    population, start_gen = load_checkpoint(checkpoint_file)
    if population is None:
        population = [Agent() for _ in range(pop_size)]
        start_gen = 0

    try:
        for gen in range(start_gen + 1, generations + 1):
            print(f"\n--- Generation {gen} ---")
            fitnesses = evaluate_population(population)
            print(f"  Best Rating: {max(fitnesses.values()):.1f}")
            
            elites = select(population, fitnesses)
            new_pop = elites[:]
            while len(new_pop) < pop_size:
                p1, p2 = random.sample(elites, 2)
                new_pop.append(mutate(crossover(p1, p2)))
            population = new_pop
            save_checkpoint(population, gen, checkpoint_file)
    except KeyboardInterrupt:
        print("\nGA training stopped safely by User.")

def getBestAgent():
    pop, _ = load_checkpoint()
    if not pop: return None
    best_agent = max(pop, key=lambda a: a.rating)
    print("\n--- BEST AGENT STATS ---")
    print(f"Weights: {best_agent.feature_weights}")
    print(f"Values: {best_agent.piece_values}")
    return best_agent

if __name__ == "__main__":
    run_ga()