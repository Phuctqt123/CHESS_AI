document.addEventListener('DOMContentLoaded', () => {
    let board = null;
    const game = new Chess();
    const moveHistoryContainer = document.getElementById('move-history');
    let userColor = 'w';
    let isAiBattle = false;

    // Custom history management
    let gameHistoryFEN = [game.fen()];
    let gameHistorySAN = [];
    let currentHistoryIndex = 0;

    // --- 1. UI & Status Management ---
    const updateStatus = (text, type) => {
        const statusText = document.getElementById('status-text');
        const statusDot = document.querySelector('.status-dot');
        if (!statusText || !statusDot) return;
        statusText.textContent = text;
        const colors = { success: '#22c55e', warning: '#f59e0b', error: '#ef4444' };
        statusDot.style.backgroundColor = colors[type];
    };

    const updateSliderLabels = () => {
        const sides = ['white', 'black'];
        sides.forEach(side => {
            const algo = document.getElementById(`${side}-algo`).value;
            const slider = document.getElementById(`${side}-slider`);
            const label = document.getElementById(`${side}-val-label`);
            const container = slider.parentElement;

            if (algo === 'none') {
                label.textContent = "Manual Play";
                container.style.opacity = "0.5";
            } else if (algo === 'mcts') {
                label.textContent = `Iterations: ${slider.value * 100}`;
                container.style.opacity = "1";
            } else {
                label.textContent = `Depth: ${slider.value}`;
                container.style.opacity = "1";
            }
        });
    };

    const checkTurnStatus = () => {
        if (game.game_over()) {
            handleGameOver();
            return;
        }
        const isWhiteTurn = game.turn() === 'w';
        const isUserTurn = game.turn() === userColor;
        const currentAlgo = isWhiteTurn ? document.getElementById('white-algo').value : document.getElementById('black-algo').value;

        // Display detailed turn info: AI Type + Color
        if (isUserTurn || currentAlgo === 'none') {
            updateStatus(`Your Turn (${isWhiteTurn ? 'White' : 'Black'})`, "success");
        } else {
            const aiName = currentAlgo === 'mcts' ? 'MCTS' : 'Alpha-Beta';
            updateStatus(`${aiName}'s Turn (${isWhiteTurn ? 'White' : 'Black'})`, "warning");
        }
    };

    const handleGameOver = () => {
        let winnerMsg = "Game Over";
        if (game.in_checkmate()) {
            const winner = game.turn() === 'w' ? "Black" : "White";
            winnerMsg = `CHECKMATE! ${winner} Wins!`;
        } else if (game.in_draw()) {
            winnerMsg = "Draw!";
        }

        updateStatus(winnerMsg, "error");

        isAiBattle = false;
        toggleAiButtons(false);

        setTimeout(() => alert(winnerMsg), 200);
    };

    // --- 2. History & Navigation Logic ---
    const renderMoveLog = () => {
        moveHistoryContainer.innerHTML = '';
        if (gameHistorySAN.length === 0) {
            moveHistoryContainer.innerHTML = '<div class="history-placeholder">Waiting for move...</div>';
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
            }
            const moveSpan = document.createElement('span');
            moveSpan.className = 'move-item';
            if (index + 1 === currentHistoryIndex) moveSpan.classList.add('active-move');
            moveSpan.textContent = move;
            moveSpan.addEventListener('click', () => jumpToMove(index + 1));
            row.appendChild(moveSpan);
            if (index % 2 === 1 || index === gameHistorySAN.length - 1) moveHistoryContainer.appendChild(row);
        });
        moveHistoryContainer.scrollTop = moveHistoryContainer.scrollHeight;
    };

    const jumpToMove = (index) => {
        isAiBattle = false;
        toggleAiButtons(false);

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
        if (currentHistoryIndex < gameHistorySAN.length) {
            gameHistoryFEN = gameHistoryFEN.slice(0, currentHistoryIndex + 1);
            gameHistorySAN = gameHistorySAN.slice(0, currentHistoryIndex);

            const targetFen = gameHistoryFEN[currentHistoryIndex];
            game.load(targetFen);
        }
        gameHistoryFEN.push(game.fen());
        gameHistorySAN.push(move.san);
        currentHistoryIndex++;
        renderMoveLog();
        checkTurnStatus();
    };

    // --- 3. AI Logic ---
    const makeComputerMove = async () => {
        if (game.game_over()) return;
        const isWhiteTurn = game.turn() === 'w';
        const algo = document.getElementById(`${isWhiteTurn ? 'white' : 'black'}-algo`).value;
        const val = document.getElementById(`${isWhiteTurn ? 'white' : 'black'}-slider`).value;

        if (algo === 'none' && !isAiBattle) return;
        if (!isAiBattle && game.turn() === userColor) return;

        try {
            const aiName = algo === 'mcts' ? 'MCTS' : 'Alpha-Beta';
            updateStatus(`${aiName} (${isWhiteTurn ? 'White' : 'Black'}) is thinking...`, "warning");

            const response = await fetch('/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fen: game.fen(), algo: algo, value: val })
            });
            const data = await response.json();
            if (data.move) {
                const move = game.move({ from: data.move.substring(0, 2), to: data.move.substring(2, 4), promotion: 'q' });
                handleNewMove(move);
                board.position(game.fen());
                checkTurnStatus(); // This will refresh to the correct turn label
                if (isAiBattle && !game.game_over()) window.setTimeout(makeComputerMove, 600);
            }
        } catch (e) { isAiBattle = false; }
    };

    // --- 4. Controls ---
    const toggleAiButtons = (running) => {
        document.getElementById('btn-ai-vs-ai').style.display = running ? 'none' : 'inline-block';
        document.getElementById('btn-stop').style.display = running ? 'inline-block' : 'none';
    };

    document.getElementById('btn-restart').addEventListener('click', () => {
        isAiBattle = false; toggleAiButtons(false);
        game.reset(); board.start();
        gameHistoryFEN = [game.fen()]; gameHistorySAN = []; currentHistoryIndex = 0;
        renderMoveLog(); checkTurnStatus();
    });

    document.getElementById('btn-switch').addEventListener('click', () => {
        board.flip(); userColor = userColor === 'w' ? 'b' : 'w';
        checkTurnStatus();
    });

    document.getElementById('btn-ai-vs-ai').addEventListener('click', () => {
        isAiBattle = true; toggleAiButtons(true);
        makeComputerMove();
    });

    document.getElementById('btn-stop').addEventListener('click', () => {
        isAiBattle = false; toggleAiButtons(false);
    });

    const boardConfig = {
        draggable: true,
        position: 'start',
        onDragStart: (s, p) => !game.game_over() && p.startsWith(userColor),
        onDrop: (source, target) => {
            const move = game.move({ from: source, to: target, promotion: 'q' });
            if (!move) return 'snapback';
            handleNewMove(move);
            window.setTimeout(makeComputerMove, 250);
        },
        onSnapEnd: () => board.position(game.fen()),
        pieceTheme: '/static/img/chesspieces/wikipedia/{piece}.png',
    };

    board = Chessboard('board', boardConfig);
    document.querySelectorAll('select, input[type="range"]').forEach(el => {
        el.addEventListener('input', updateSliderLabels);
    });

    updateSliderLabels();
    checkTurnStatus();
});