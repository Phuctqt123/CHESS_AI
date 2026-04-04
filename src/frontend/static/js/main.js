document.addEventListener('DOMContentLoaded', () => {
    let board = null; 
    const game = new Chess(); 
    const moveHistory = document.getElementById('move-history'); 
    let moveCount = 1; 
    let userColor = 'w'; 
    let isAiThinking = false;
    let pendingMove = null; 
    let botIsRunning = false;
    const promotionModal = document.getElementById('promotion-modal');

    // --- Xử lý Giao diện Setup ---
    const gameModeSelect = document.getElementById('game-mode');
    const pveSetup = document.getElementById('pve-setup');
    const eveSetup = document.getElementById('eve-setup');
    const depthSlider = document.getElementById('depth-slider');
    const depthValueDisplay = document.getElementById('depth-value');

    if (depthSlider && depthValueDisplay) {
        depthSlider.addEventListener('input', () => {
            depthValueDisplay.textContent = depthSlider.value;
        });
    }

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
        // Fix double trigger: Chặn handleGameOver ở đây, nhường cho checkTurnStatus
        if (game.game_over() || isAiThinking) {
            return -1;
        }

        isAiThinking = true;
        let selectedAlgo;

        if (gameModeSelect.value === 'pve') {
            selectedAlgo = document.getElementById('difficulty-select').value;
        } else {
            selectedAlgo = (game.turn() === 'w') ? 
                document.getElementById('white-algo').value : 
                document.getElementById('black-algo').value;
        }

        try {
            const currentDepth = depthSlider ? parseInt(depthSlider.value) : 3;
            // Gửi CẢ algo và depth để chiều lòng cả 2 người
            const response = await fetch('/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    fen: game.fen(), 
                    algo: selectedAlgo,
                    depth: currentDepth
                })
            });

            const data = await response.json();

            if (!data || !data.move) {
                console.error("Invalid API response:", data);
                updateStatus("AI Error or No moves", "error");
                isAiThinking = false;
                return -2;
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
            return 0;

        } catch (error) {
            console.error("API error:", error);
            updateStatus("Connection Lost", "error");
            isAiThinking = false;
            return -3;
        }
    };

    // --- Các hàm tiện ích ---
    const recordMove = (move, count) => {
        if (count === 1) moveHistory.innerHTML = ''; 

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
        
        if (botIsRunning || gameModeSelect.value === 'eve') {
            const currentTurnAlgo = game.turn() === 'w' ? 'White AI' : 'Black AI';
            updateStatus(`Bot vs Bot: ${currentTurnAlgo} thinking...`, "warning");
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
            winner = game.turn() === 'w' ? "Black" : "White";
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

    // --- Tương tác Bàn cờ ---
    const onDragStart = (source, piece) => {
        if (game.game_over() || botIsRunning) return false;
        if (game.turn() !== userColor) return false;
        
        // Cập nhật luật switch-sides của đồng đội
        const canDrag = (userColor === 'w' && piece.search(/^w/) !== -1) ||
                        (userColor === 'b' && piece.search(/^b/) !== -1);
        
        if (canDrag) onMouseoverSquare(source, piece);
        return canDrag;
    };

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
        if (sqElement) sqElement.classList.add(isCapture ? 'highlight-capture' : 'highlight-move');
    };

    const onMouseoverSquare = (square, piece) => {
        if (game.turn() !== userColor || botIsRunning) return;
        const moves = game.moves({ square: square, verbose: true });
        if (moves.length === 0) return;

        const sourceSq = document.querySelector('#board .square-' + square);
        if (sourceSq) sourceSq.classList.add('highlight-source');

        for (let i = 0; i < moves.length; i++) {
            highlightSquare(moves[i].to, moves[i].flags.includes('c'));
        }
    };

    const onMouseoutSquare = () => removeHighlights();

    const onDrop = (source, target) => {
        removeHighlights();
        
        const moveAttempt = game.move({ from: source, to: target, promotion: 'q' });
        if (moveAttempt === null) return 'snapback';
        game.undo();

        const piece = game.get(source);
        const isPromotion = piece && piece.type === 'p' && 
                          ((piece.color === 'w' && target[1] === '8') || 
                           (piece.color === 'b' && target[1] === '1'));

        if (isPromotion) {
            showPromotionModal(source, target);
            return 'snapback'; 
        }

        const move = game.move({ from: source, to: target, promotion: 'q' });
        recordMove(move.san, moveCount);
        moveCount++;
        
        checkTurnStatus(); 
        window.setTimeout(makeComputerMove, 250);
    };

    // --- Promotion Modal Logic ---
    const showPromotionModal = (source, target) => {
        pendingMove = { source, target };
        const color = game.turn(); 
        const pieceNames = { 'q': 'Queen', 'r': 'Rook', 'b': 'Bishop', 'n': 'Knight' };
        
        Object.keys(pieceNames).forEach(p => {
            const img = document.getElementById(`promo-${p}`);
            if (img) img.src = `/static/img/chesspieces/wikipedia/${color}${p.toUpperCase()}.png`;
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

    const onSnapEnd = () => board.position(game.fen());

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

    // --- Xử lý Nút Bấm Gộp ---
    document.getElementById('start-btn').addEventListener('click', () => {
        game.reset();
        board.start();
        moveHistory.innerHTML = '<div class="history-placeholder">Waiting for the first move...</div>';
        moveCount = 1;
        userColor = 'w';
        isAiThinking = false;
        pendingMove = null;
        if(promotionModal) promotionModal.style.display = 'none';
        
        if (botIsRunning) {
            botIsRunning = false;
            document.querySelector('.bot-v-bot').innerHTML = '<i class="fas fa-robot"></i> Bot vs Bot';
        }
        checkTurnStatus();
    });

    document.querySelector('.flip-board').addEventListener('click', () => {
        board.flip();
    });

    document.querySelector('.switch-sides').addEventListener('click', () => {
        if (botIsRunning) return;
        userColor = userColor === 'w' ? 'b' : 'w';
        board.flip();
        checkTurnStatus();
        if (game.turn() !== userColor) {
            makeComputerMove();
        }
    });

    const botVBot = async () => {
        if (botIsRunning) return;
        botIsRunning = true;
        
        // Tự động chuyển UI sang chế độ EvE
        gameModeSelect.value = 'eve';
        gameModeSelect.dispatchEvent(new Event('change'));

        const botBtn = document.querySelector('.bot-v-bot');
        
        while (botIsRunning) {
            const result = await makeComputerMove();
            if (result !== 0) {
                botIsRunning = false;
                botBtn.innerHTML = '<i class="fas fa-robot"></i> Bot vs Bot';
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 600));
        }
    };

    const botBtn = document.querySelector('.bot-v-bot');
    botBtn.addEventListener('click', () => {
        if (botIsRunning) {
            botIsRunning = false;
            botBtn.innerHTML = '<i class="fas fa-robot"></i> Bot vs Bot';
        } else {
            botBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Bot vs Bot';
            botVBot();
        }
    });
});