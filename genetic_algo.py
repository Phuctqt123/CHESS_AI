import random
import copy
import chess
import pickle
import os
from multiprocessing import Pool, cpu_count

legal_moves_cache = {}

class Agent:
    def __init__(self):
        self.rating: float = 1000.0
        self.n_features = 2
        self.feature_weights: list[float] = []
        self.piece_values: dict[int, float] = {
            chess.PAWN: 0.0,
            chess.KNIGHT: 0.0,
            chess.BISHOP: 0.0,
            chess.ROOK: 0.0,
            chess.QUEEN: 0.0,
            chess.KING: 0.0
        }
        self.piece_tables = {
            chess.PAWN: [],
            chess.KNIGHT: [],
            chess.BISHOP: [],
            chess.ROOK: [],
            chess.QUEEN: [],
            chess.KING: []
        }
        self.__eval_cache = {}
        self.__tt_cache = {}
        self.__randomize_values()

    def __randomize_values(self):
        self.feature_weights = [
            random.uniform(0.0, 2.0),   # material weight
            random.uniform(0.0, 2.0)    # piece-square table weight
        ]

        self.piece_values = {
            chess.PAWN: random.uniform(0, 200),
            chess.KNIGHT: random.uniform(0, 500),
            chess.BISHOP: random.uniform(0, 500),
            chess.ROOK: random.uniform(0, 800),
            chess.QUEEN: random.uniform(0, 1200),
            chess.KING: 0
        }

        for piece_type in self.piece_tables:
            bound = 100
            self.piece_tables[piece_type] = [
                random.uniform(-bound, bound) for _ in range(64)
            ]

    def eval_board(self, board: chess.Board):
        key = board.board_fen
        if key in self.__eval_cache:
            return self.__eval_cache[key]

        if board.is_checkmate():
            res = board.result()
            if res == '1-0':
                return float('inf')
            elif res == '0-1' :
                return float('-inf')

        if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(3):
            return 0.0

        score = 0
        mat_weight = self.feature_weights[0]
        piece_position_weight = self.feature_weights[1]

        for square, piece in board.piece_map().items():
            base_piece_value = self.piece_values[piece.piece_type]
            pst = self.piece_tables[piece.piece_type]
            square = square if piece.color == chess.WHITE else chess.square_mirror(square)
            value = base_piece_value * mat_weight + pst[square] * piece_position_weight
            score += value if piece.color == chess.WHITE else -value

        self.__eval_cache[key] = score
        return score

    def clearEvalCache(self):
        self.__eval_cache.clear()

    def __order_moves(self, board):
        key = board.fen()
        if key in legal_moves_cache:
            moves = legal_moves_cache[key]
        else:
            moves = list(board.legal_moves)
            legal_moves_cache[key] = moves

        def move_score(move):
            board.push(move)
            key = board._transposition_key()
            score = self.__eval_cache.get(key, 0.0)
            board.pop()
            return score

        return sorted(
            moves,
            key=move_score,
            reverse=(board.turn == chess.WHITE)
        )

    def __minimax(self, board: chess.Board,  depth, alpha=float('-inf'), beta=float('inf')):
        key = (board.fen(), depth)
        if key in self.__tt_cache:
            return self.__tt_cache[key]

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
                if alpha >= beta:
                    break
            self.__tt_cache[key] = value
            return value
        else:
            value = float('inf')
            for move in self.__order_moves(board):
                board.push(move)
                value = min(value, self.__minimax(board, depth - 1, alpha, beta))
                board.pop()
                beta = min(beta, value)
                if beta <= alpha:
                    break
            self.__tt_cache[key] = value
            return value

    def evaluate_move(self, args):
        fen, move_uci, depth = args
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_uci)

        board.push(move)
        score = self.__minimax(board, depth - 1)
        board.pop()
        return move_uci, score

    def get_best_moves(self, board: chess.Board, depth: int = 3, parallelize=False):
        fen = board.fen()
        if fen in legal_moves_cache:
            moves = legal_moves_cache[fen]
        else:
            moves = list(board.legal_moves)
            legal_moves_cache[fen] = moves

        if parallelize:
            args = [(fen, move.uci(), depth) for move in moves]
            with Pool(cpu_count() - 2) as pool:
                results = pool.map(self.evaluate_move, args)
        else:
            results = []
            for move in moves:
                args = (fen, move.uci(), depth)
                res = self.evaluate_move(args)
                results.append(res)

        move_scores = {chess.Move.from_uci(m): s for m, s in results}
        scores = move_scores.values()
        best_score = max(scores) if board.turn == chess.WHITE else min(scores)
        best_moves = [m for m, s in move_scores.items() if s == best_score]
        return best_moves

    def get_move(self, board: chess.Board, depth: int = 3, parallelize=False):
        moves = self.get_best_moves(board, depth, parallelize)
        if not moves:
            return None
        return random.choice(moves) 


def play_game(agent1: Agent, agent2: Agent, max_n_moves: int =50, depth: int = 3):
    board = chess.Board()
    white = agent1
    black = agent2

    for _ in range(max_n_moves*2):
        if board.is_game_over():
            match board.result():
                case '1-0':
                    return 1.0
                case '0-1' :
                    return -1.0
                case '1/2-1/2':
                    return 0.5
                case _ :
                    break

        if board.turn == chess.WHITE:
            move_uci = white.get_move(board, depth, parallelize=True)
        else:
            move_uci = black.get_move(board, depth, parallelize=True)

        board.push(move_uci)
    return 0.0

def update_elo(r_a, r_b, game_res):
    if abs(game_res - 0.0) < 1e-10:
        return r_a

    expected_score = 1 / ( 1 + 10 ** ((r_b - r_a)/400) )
    score = game_res + 1.0 if game_res < 0.0 else game_res

    if r_a < 1700:
        k = 40
    elif r_a > 2400:
        k = 10
    else:
        k = 20

    new_rating = r_a + k * (score - expected_score)
    return new_rating

def play_match(args):
    i, j, a, b = args
    result = play_game(a, b)

    r_a = a.rating
    r_b = b.rating
    r_a_delta = update_elo(r_a, r_b, result) - r_a
    r_b_delta = update_elo(r_b, r_a, -result) - r_b

    return (i, r_a_delta, j, r_b_delta)

def evaluate_population(population: list[Agent], games_per_agent=5):
    indices = list(range(len(population)))
    matchups = []
    deltas = [0.0 for _ in population]

    for i in indices:
        opps = random.sample(indices, games_per_agent)
        while i in opps:
            opps = random.sample(indices, games_per_agent)
        for j in opps:
            matchups.append((i, j, population[i], population[j]))

    results = [play_match(matchup) for matchup in matchups]

    for i, d_i, j, d_j in results:
        deltas[i] += d_i
        deltas[j] += d_j

    ratings = {}
    for i, agent in enumerate(population):
        agent.rating += deltas[i]
        ratings[agent] = agent.rating

    return ratings

def select(population, fitnesses, top_k=10):
    paired = [(agent, fitnesses[agent]) for agent in population]
    paired.sort(key=lambda x: x[1], reverse=True)
    selected = [agent for agent, _ in paired[:top_k]]
    return selected

def crossover(parent1, parent2):
    child = copy.deepcopy(parent1)
    child.clearEvalCache()

    for i in range(len(child.feature_weights)):
        if random.random() < 0.5:
            child.feature_weights[i] = parent2.feature_weights[i]

    for p in child.piece_values:
        if random.random() < 0.5:
            child.piece_values[p] = parent2.piece_values[p]

    for p in child.piece_tables:
        for i in range(64):
            if random.random() < 0.5:
                child.piece_tables[p][i] = parent2.piece_tables[p][i]

    return child

def mutate(agent: Agent, rate=0.1):
    for i in range(len(agent.feature_weights)):
        if random.random() < rate:
            agent.feature_weights[i] += random.uniform(-0.2, 0.2)

    for p in agent.piece_values:
        if random.random() < rate:
            agent.piece_values[p] += random.uniform(-20, 20)

    for p in agent.piece_tables:
        for i in range(64):
            if random.random() < rate:
                agent.piece_tables[p][i] += random.uniform(-5, 5)

    return agent

def save_checkpoint(population, gen, filename="ga_checkpoint.pkl"):
    print(f'Saving to {filename}...')
    with open(filename, "wb") as f:
        pickle.dump({
            "generation": gen,
            "population": population
        }, f)

def load_checkpoint(filename="ga_checkpoint.pkl"):
    print('Loading from ' + filename + '...')
    if not os.path.exists(filename):
        return None, 0
    with open(filename, "rb") as f:
        data = pickle.load(f)
    return data["population"], data["generation"]

def run_ga(pop_size=30, generations=200, checkpoint_file="ga_checkpoint.pkl"):
    population, start_gen = load_checkpoint(checkpoint_file)

    if population is None:
        print("Starting fresh...")
        population = [Agent() for _ in range(pop_size)]
        start_gen = 0
    else:
        print(f"Resuming from generation {start_gen}")

    for gen in range(start_gen + 1, generations + 1):
        print(f"Generation {gen}")

        print('Agents are fighting...')
        fitnesses = evaluate_population(population)
        for agent in fitnesses:
            print(fitnesses[agent], end=' ')
        print()
        print("Best elo:", max(fitnesses.values()))

        print('Filtering agents...')
        elites = select(population, fitnesses, top_k=3)

        new_population = elites[:]

        print('Repopulating generation...')
        while len(new_population) < pop_size:
            p1, p2 = random.sample(elites, 2)
            child = crossover(p1, p2)
            child = mutate(child)
            new_population.append(child)

        population = new_population
        save_checkpoint(population, gen, checkpoint_file)

    return population

def getBestAgent():
    pop, _ = load_checkpoint()
    ratings = [agent.rating for agent in pop]
    best_rating = max(ratings)
    best_agents = [agent for agent in pop if agent.rating == best_rating]
    chosen_agent = best_agents[0]
    print(chosen_agent.feature_weights)
    print(chosen_agent.piece_values)
    print(chosen_agent.piece_tables)
    return chosen_agent

def main():
    run_ga()

if __name__ == "__main__":
    main()