// Wait for the DOM to be fully loaded before executing code
document.addEventListener('DOMContentLoaded', () => {
    let board = null; // Initialize the chessboard
    const game = new Chess(); // Create new Chess.js game instance
    const moveHistory = document.getElementById('move-history'); // Get move history container
    let moveCount = 1; // Initialize the move count
    let userColor = 'w'; // Initialize the user's color as white
    let isAiThinking = false;
    let pendingMove = null; // Store pending promotion move
    const promotionModal = document.getElementById('promotion-modal');

    // --- Xử lý Giao diện Setup ---
    const gameModeSelect = document.getElementById('game-mode');
    const pveSetup = document.getElementById('pve-setup');
    const eveSetup = document.getElementById('eve-setup');

    // Ẩn/hiện menu tùy theo chế độ chơi
    gameModeSelect.addEventListener('change', (e) => {
        if (e.target.value === 'pve') {
            pveSetup.style.display = 'block';
            eveSetup.style.display = 'none';
        } else {
            pveSetup.style.display = 'none';
            eveSetup.style.display = 'block';
        }
    });

    // --- Lõi AI xử lý nước đi ---
    const makeComputerMove = async () => {
        if (game.game_over() || isAiThinking) {
            return;
        }

        isAiThinking = true;
        let selectedAlgo;

        // Xác định thuật toán dựa trên chế độ chơi
        if (gameModeSelect.value === 'pve') {
            selectedAlgo = document.getElementById('difficulty-select').value;
        } else {
            // Nếu là EvE: Trắng lấy menu trắng, Đen lấy menu đen
            selectedAlgo = (game.turn() === 'w') ? 
                document.getElementById('white-algo').value : 
                document.getElementById('black-algo').value;
        }

        try {
            const response = await fetch('/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    fen: game.fen(), 
                    algo: selectedAlgo
                })
            });

            const data = await response.json();

            if (!data || !data.move) {
                console.error("AI Error or no valid moves left.");
                updateStatus("AI Error", "error");
                isAiThinking = false;
                return;
            }

            const moveObj = {
                from: data.move.substring(0, 2),
                to: data.move.substring(2, 4),
                promotion: data.move.length > 4 ? data.move.substring(4, 5) : 'q'
            };

            const move = game.move(moveObj);

            if (move !== null) {
                board.position(game.fen());
                recordMove(move.san, moveCount);
                moveCount++;
                checkTurnStatus();
            }

            isAiThinking = false;

            // KÍCH HOẠT VÒNG LẶP CHO MÁY VS MÁY
            if (gameModeSelect.value === 'eve' && !game.game_over()) {
                setTimeout(makeComputerMove, 500);
            }

        } catch (error) {
            console.error("Mất kết nối với Server:", error);
            updateStatus("Connection Lost", "error");
            isAiThinking = false;
        }
    };

    // --- Các hàm tiện ích (Vẽ lịch sử, check trạng thái) ---
    const recordMove = (move, count) => {
        if (count === 1) moveHistory.innerHTML = ''; // Clear placeholder on first move

        const isWhite = count % 2 === 1;
        const moveNumber = Math.ceil(count / 2);

        if (isWhite) {
            const moveRow = document.createElement('div');
            moveRow.className = 'move-row';
            moveRow.innerHTML = `
                <span class="move-number">${moveNumber}.</span>
                <span class="white-move">${move}</span>
            `;
            moveHistory.appendChild(moveRow);
        } else {
            const lastRow = moveHistory.lastElementChild;
            if (lastRow) {
                const blackMove = document.createElement('span');
                blackMove.className = 'black-move';
                blackMove.textContent = move;
                lastRow.appendChild(blackMove);
            }
        }
        moveHistory.scrollTop = moveHistory.scrollHeight;
    };

    const checkTurnStatus = () => {
        if (game.game_over()) {
            handleGameOver();
            return;
        }
        
        if (gameModeSelect.value === 'eve') {
            const currentTurnAlgo = game.turn() === 'w' ? 'White' : 'Black';
            updateStatus(`AI vs AI: ${currentTurnAlgo} is thinking...`, "warning");
        } else {
            const isUserTurn = game.turn() === userColor;
            const turnText = isUserTurn ? `Your Turn (${userColor === 'w' ? 'White' : 'Black'})` : "AI's Turn (Thinking)";
            updateStatus(turnText, isUserTurn ? "success" : "warning");
        }
    };

    const updateStatus = (text, type) => {
        const statusText = document.getElementById('status-text');
        const statusDot = document.querySelector('.status-dot');
        statusText.textContent = text;
        
        // Dynamic colors based on type
        if (type === 'warning') {
            statusDot.style.backgroundColor = '#f59e0b';
            statusDot.style.boxShadow = '0 0 8px #f59e0b';
        } else if (type === 'error') {
            statusDot.style.backgroundColor = '#ef4444';
            statusDot.style.boxShadow = '0 0 8px #ef4444';
        } else if (type === 'success') {
            statusDot.style.backgroundColor = '#22c55e';
            statusDot.style.boxShadow = '0 0 8px #22c55e';
        }
    };

    const handleGameOver = () => {
        let status = "Game Over";
        let winner = "";

        if (game.in_checkmate()) {
            winner = game.turn() === 'w' ? "Black (AI)" : "White (You)";
            if (gameModeSelect.value === 'eve') {
                winner = game.turn() === 'w' ? "Black (MCTS)" : "White (Alpha-Beta)";
            }
            status = `CHECKMATE! Winner: ${winner}`;
        } else if (game.in_draw()) {
            status = "Game Over: DRAW!";
            if (game.in_stalemate()) status += " (Stalemate)";
            else if (game.insufficient_material()) status += " (Insufficient Material)";
            else if (game.in_threefold_repetition()) status += " (Repetition)";
        }

        updateStatus(status, "error");
        setTimeout(() => alert(status), 500);
    };

    // --- Highlighting Logic ---
    const removeHighlights = () => {
        const squares = document.querySelectorAll('#board .square-55d63');
        squares.forEach(sq => {
            sq.classList.remove('highlight-move');
            sq.classList.remove('highlight-capture');
            sq.classList.remove('highlight-source');
        });
    };

    const highlightSquare = (square, isCapture) => {
        const sqElement = document.querySelector('#board .square-' + square);
        if (sqElement) {
            sqElement.classList.add(isCapture ? 'highlight-capture' : 'highlight-move');
        }
    };

    const onMouseoverSquare = (square, piece) => {
        // Exit if it's not the user's turn or game mode is EvE
        if (game.turn() !== userColor || gameModeSelect.value === 'eve') return;

        // Get list of possible moves for this square
        const moves = game.moves({ square: square, verbose: true });

        // Exit if there are no moves available for this square
        if (moves.length === 0) return;

        // Highlight the source square
        const sourceSq = document.querySelector('#board .square-' + square);
        if (sourceSq) sourceSq.classList.add('highlight-source');

        // Highlight the destination squares
        for (let i = 0; i < moves.length; i++) {
            highlightSquare(moves[i].to, moves[i].flags.includes('c'));
        }
    };

    const onMouseoutSquare = (square, piece) => {
        removeHighlights();
    };

    // --- Tương tác Bàn cờ ---
    const onDragStart = (source, piece) => {
        if (game.game_over()) return false;
        if (gameModeSelect.value === 'eve') return false; // Khóa không cho cầm cờ nếu là AI vs AI
        
        // User can only drag on their turn
        if (game.turn() !== userColor) return false;
        
        // Allow the user to drag only their own pieces
        const canDrag = (userColor === 'w' && piece.search(/^w/) !== -1) ||
                        (userColor === 'b' && piece.search(/^b/) !== -1);
        
        if (canDrag) {
            onMouseoverSquare(source, piece);
        }
        return canDrag;
    };

    const onDrop = (source, target) => {
        removeHighlights();
        
        // Check if move is legal temporarily
        const moveAttempt = game.move({
            from: source,
            to: target,
            promotion: 'q' // Temporary to check legality
        });

        if (moveAttempt === null) return 'snapback';
        
        // Undo the temporary move
        game.undo();

        // Check for promotion
        const piece = game.get(source);
        const isPromotion = piece && piece.type === 'p' && 
                          ((piece.color === 'w' && target[1] === '8') || 
                           (piece.color === 'b' && target[1] === '1'));

        if (isPromotion) {
            showPromotionModal(source, target);
            return 'snapback'; // Khựng lại để chờ chọn phong cấp
        }

        // Thực hiện nước đi thật
        const move = game.move({ from: source, to: target, promotion: 'q' });
        recordMove(move.san, moveCount);
        moveCount++;
        
        checkTurnStatus(); 
        window.setTimeout(makeComputerMove, 250);
    };

    // --- Promotion Modal Logic ---
    const showPromotionModal = (source, target) => {
        pendingMove = { source, target };
        
        // Update images based on user color
        const color = game.turn(); // 'w' or 'b'
        const pieceNames = { 'q': 'Queen', 'r': 'Rook', 'b': 'Bishop', 'n': 'Knight' };
        
        Object.keys(pieceNames).forEach(p => {
            const img = document.getElementById(`promo-${p}`);
            if (img) {
                img.src = `/static/img/chesspieces/wikipedia/${color}${p.toUpperCase()}.png`;
            }
        });
        
        promotionModal.style.display = 'flex';
    };

    const handlePromotion = (source, target, piece) => {
        const move = game.move({ from: source, to: target, promotion: piece });
        if (move === null) return;

        board.position(game.fen());
        recordMove(move.san, moveCount);
        moveCount++;
        
        checkTurnStatus();
        window.setTimeout(makeComputerMove, 250);
    };

    // Add listeners to promotion options
    document.querySelectorAll('.promotion-option').forEach(option => {
        option.addEventListener('click', () => {
            const piece = option.getAttribute('data-piece');
            if (pendingMove) {
                handlePromotion(pendingMove.source, pendingMove.target, piece);
                pendingMove = null;
                promotionModal.style.display = 'none';
            }
        });
    });

    const onSnapEnd = () => {
        board.position(game.fen());
    };

    // Configuration options for the chessboard
    const boardConfig = {
        showNotation: true,
        draggable: true,
        position: 'start',
        onDragStart,
        onDrop,
        onSnapEnd,
        onMouseoverSquare,
        onMouseoutSquare,
        pieceTheme: '/static/img/chesspieces/wikipedia/{piece}.png',
        moveSpeed: 'fast',
    };

    board = Chessboard('board', boardConfig);

    // --- Các nút chức năng ---
    document.getElementById('start-btn').addEventListener('click', () => {
        game.reset();
        board.start();
        moveHistory.innerHTML = '<div class="history-placeholder">Waiting for the first move...</div>';
        moveCount = 1;
        userColor = 'w';
        isAiThinking = false;
        pendingMove = null;
        if(promotionModal) promotionModal.style.display = 'none';
        
        checkTurnStatus();

        // NẾU ĐANG LÀ MÁY VS MÁY, MỒI LƯỢT ĐI ĐẦU TIÊN
        if (gameModeSelect.value === 'eve') {
            setTimeout(makeComputerMove, 500);
        }
    });

    document.querySelector('.flip-board').addEventListener('click', () => {
        if (gameModeSelect.value === 'eve') return; // Không cho lật bàn ở chế độ EvE
        board.flip();
        userColor = userColor === 'w' ? 'b' : 'w';
        checkTurnStatus();
        
        if (game.turn() !== userColor) {
            makeComputerMove();
        }
    });
});