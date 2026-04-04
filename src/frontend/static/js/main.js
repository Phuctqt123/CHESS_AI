document.addEventListener('DOMContentLoaded', () => {
    let board = null; 
    const game = new Chess(); 
    const moveHistoryContainer = document.getElementById('move-history'); 
    let userColor = 'w'; 
    let isAiThinking = false;
    let pendingMove = null; 
    let botIsRunning = false;
    const promotionModal = document.getElementById('promotion-modal');

    // --- Quản lý lịch sử nước đi ---
    let gameHistoryFEN = [game.fen()];
    let gameHistorySAN = [];
    let currentHistoryIndex = 0;

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

    // --- Xử lý Ghi log và Quay lui lịch sử (Jump to Move) ---
    const renderMoveLog = () => {
        moveHistoryContainer.innerHTML = '';
        if (gameHistorySAN.length === 0) {
            moveHistoryContainer.innerHTML = '<div class="history-placeholder">Waiting for the first move...</div>';
            return;
        }

        let row;
        gameHistorySAN.forEach((move, index) => {
            if (index % 2 === 0) {
                row = document.createElement('div');
                row.className = 'move-row';
                const num = document.createElement('span');
                num.className = 'move-number';
                num.textContent = `${Math.floor(index / 2) + 1}.`;
                row.appendChild(num);
                moveHistoryContainer.appendChild(row);
            }
            const moveSpan = document.createElement('span');
            moveSpan.className = (index % 2 === 0) ? 'white-move' : 'black-move';
            
            // Highlight nước đi hiện tại đang xem
            if (index + 1 === currentHistoryIndex) {
                moveSpan.style.color = 'var(--primary)';
                moveSpan.style.fontWeight = 'bold';
            }
            
            moveSpan.textContent = move;
            moveSpan.style.cursor = 'pointer';
            // Click vào nước đi để lùi lịch sử
            moveSpan.addEventListener('click', () => jumpToMove(index + 1));
            row.appendChild(moveSpan);
        });
        moveHistoryContainer.scrollTop = moveHistoryContainer.scrollHeight;
    };

    const jumpToMove = (index) => {
        // Dừng bot nếu đang đánh nhau
        if (botIsRunning) {
            botIsRunning = false;
            document.querySelector('.bot-v-bot').style.display = 'inline-flex';
            document.getElementById('btn-stop').style.display = 'none';
        }

        currentHistoryIndex = index;
        game.reset();
        for (let i = 0; i < index; i++) {
            game.move(gameHistorySAN[i]);
        }
        board.position(game.fen());
        renderMoveLog();
        checkTurnStatus();
    };

    const handleNewMove = (move) => {
        // Nếu người chơi đi nhánh mới từ quá khứ, cắt bỏ các nước tương lai
        if (currentHistoryIndex < gameHistorySAN.length) {
            gameHistoryFEN = gameHistoryFEN.slice(0, currentHistoryIndex + 1);
            gameHistorySAN = gameHistorySAN.slice(0, currentHistoryIndex);
        }
        gameHistoryFEN.push(game.fen());
        gameHistorySAN.push(move.san);
        currentHistoryIndex++;
        renderMoveLog();
        checkTurnStatus();
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
        
        if (botIsRunning) {
            botIsRunning = false;
            document.querySelector('.bot-v-bot').style.display = 'inline-flex';
            document.getElementById('btn-stop').style.display = 'none';
        }
        
        setTimeout(() => alert(status), 500);
    };

    // --- Lõi AI xử lý nước đi ---
    const makeComputerMove = async () => {
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
                handleNewMove(move); // Ghi đè bằng hàm lưu lịch sử mới
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

    // --- Tương tác Bàn cờ (Highlight & Drag-Drop của bạn) ---
    const onDragStart = (source, piece) => {
        if (game.game_over() || botIsRunning) return false;
        if (game.turn() !== userColor) return false;
        
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
        handleNewMove(move);
        window.setTimeout(makeComputerMove, 250);
    };

    // --- Promotion Modal Logic (Của bạn) ---
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
        handleNewMove(move);
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

    // --- Cấu hình các nút điều khiển ---
    document.getElementById('start-btn').addEventListener('click', () => {
        game.reset();
        board.start();
        
        // Reset lịch sử
        gameHistoryFEN = [game.fen()];
        gameHistorySAN = [];
        currentHistoryIndex = 0;
        renderMoveLog();
        
        userColor = 'w';
        isAiThinking = false;
        pendingMove = null;
        if(promotionModal) promotionModal.style.display = 'none';
        
        if (botIsRunning) {
            botIsRunning = false;
            document.querySelector('.bot-v-bot').style.display = 'inline-flex';
            document.getElementById('btn-stop').style.display = 'none';
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

    // --- Cập nhật Bot vs Bot với nút Stop riêng ---
    const botVBot = async () => {
        if (botIsRunning) return;
        botIsRunning = true;
        
        // Đổi nút hiển thị
        document.querySelector('.bot-v-bot').style.display = 'none';
        document.getElementById('btn-stop').style.display = 'inline-flex';

        // Tự động chuyển UI sang chế độ EvE
        gameModeSelect.value = 'eve';
        gameModeSelect.dispatchEvent(new Event('change'));
        
        while (botIsRunning) {
            const result = await makeComputerMove();
            if (result !== 0) {
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 600));
        }

        botIsRunning = false;
        document.querySelector('.bot-v-bot').style.display = 'inline-flex';
        document.getElementById('btn-stop').style.display = 'none';
    };

    document.querySelector('.bot-v-bot').addEventListener('click', botVBot);

    document.getElementById('btn-stop').addEventListener('click', () => {
        botIsRunning = false;
        document.querySelector('.bot-v-bot').style.display = 'inline-flex';
        document.getElementById('btn-stop').style.display = 'none';
        checkTurnStatus();
    });
});