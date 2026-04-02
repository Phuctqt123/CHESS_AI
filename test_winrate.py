import sys
import os
import time
import chess

# Cấu hình đường dẫn để import
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.backend.engine import get_best_move_alphabeta, get_best_move_mcts, get_best_move_genetic

# ==========================================
# CẤU HÌNH SỐ VÁN ĐẤU
# ==========================================
NUM_GAMES_PER_MATCHUP = 10  # Số ván cho MỖI cặp đấu (Tổng 3 cặp là 30 ván)

def get_move_for_bot(bot_name, fen):
    """Phân loại và gọi đúng hàm dựa trên tên Bot"""
    if "Genetic" in bot_name:
        return get_best_move_genetic(fen, depth=4)
    elif "Alpha-Beta" in bot_name:
        return get_best_move_alphabeta(fen, depth=2)
    elif "MCTS" in bot_name:
        return get_best_move_mcts(fen, iterations=150)
    return None

def play_one_game(white_bot, black_bot, game_num):
    board = chess.Board()
    moves_played = 0
    
    while not board.is_game_over():
        if board.turn == chess.WHITE:
            uci = get_move_for_bot(white_bot, board.fen())
        else:
            uci = get_move_for_bot(black_bot, board.fen())
            
        if uci:
            board.push(chess.Move.from_uci(uci))
            moves_played += 1
        else:
            break
            
    return board.result(), moves_played

def run_matchup(bot1, bot2):
    print(f"\n" + "="*60)
    print(f" TRẬN ĐẤU: {bot1} vs {bot2} ({NUM_GAMES_PER_MATCHUP} ván)")
    print("="*60)
    
    bot1_wins = 0
    bot2_wins = 0
    draws = 0
    start_time = time.time()
    
    for i in range(1, NUM_GAMES_PER_MATCHUP + 1):
        # Đổi bên công bằng: Ván lẻ bot 1 cầm Trắng, ván chẵn bot 1 cầm Đen
        if i % 2 != 0:
            white, black = bot1, bot2
        else:
            white, black = bot2, bot1
            
        res, moves = play_one_game(white, black, i)
        print(f"  Ván {i}: {white} (Trắng) vs {black} (Đen) | {moves} nước | Kết quả: {res}")
        
        # Thống kê
        if res == "1-0":
            if white == bot1: bot1_wins += 1
            else: bot2_wins += 1
        elif res == "0-1":
            if black == bot1: bot1_wins += 1
            else: bot2_wins += 1
        else:
            draws += 1
            
    total_time = time.time() - start_time
    
    # IN BẢNG TỔNG KẾT CHO CẶP ĐẤU NÀY
    print(f"\n --- THỐNG KÊ KẾT QUẢ: {bot1} vs {bot2} ---")
    print(f" Tổng thời gian: {total_time:.2f} giây (Trung bình {total_time/NUM_GAMES_PER_MATCHUP:.2f}s/ván)")
    print(f" [{bot1}] Thắng : {bot1_wins} ván ({bot1_wins/NUM_GAMES_PER_MATCHUP*100:.1f}%)")
    print(f" [{bot2}] Thắng : {bot2_wins} ván ({bot2_wins/NUM_GAMES_PER_MATCHUP*100:.1f}%)")
    print(f" Hòa (Draws)  : {draws} ván ({draws/NUM_GAMES_PER_MATCHUP*100:.1f}%)")

if __name__ == '__main__':
    # DANH SÁCH 3 CẶP ĐẤU
    matchups = [
        ("MCTS", "Alpha-Beta Pruning"),
        ("MCTS", "Alpha-Beta Pruning + Genetic"),
        ("Alpha-Beta", "Alpha-Beta Pruning + Genetic")
    ]
    
    print("\n" + "*"*60)
    print(" KHỞI ĐỘNG GIẢI ĐẤU KIỂM THỬ TỰ ĐỘNG ")
    print("*"*60)
    
    for b1, b2 in matchups:
        run_matchup(b1, b2)
        
    print("\n" + "*"*60)
    print(" ĐÃ HOÀN THÀNH TOÀN BỘ CÁC CẶP ĐẤU!")
    print("*"*60 + "\n")