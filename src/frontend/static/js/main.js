document.addEventListener('DOMContentLoaded', () => {
    let board = null;
    const game = new Chess();
    const moveHistory = document.getElementById('move-history');
    let moveCount = 1;
    let isAiBattle = false;
    let userColor = 'w'; // Default: User plays White

    // Update UI Labels based on selected algorithm and slider value
    const updateSliderLabels = () => {
        const sides = ['white', 'black'];
        sides.forEach(side => {
            const algo = document.getElementById(`${side}-algo`).value;
            const val = document.getElementById(`${side}-slider`).value;
            const label = document.getElementById(`${side}-val-label`);
            const container = document.getElementById(`${side}-slider`).parentElement;

            if (algo === 'none') {
                label.textContent = "Manual Play";
                container.style.opacity = "0.5";
            } else if (algo === 'mcts') {
                label.textContent = `Iterations: ${val * 100}`;
                container.style.opacity = "1";
            } else {
                label.textContent = `Depth: ${val}`;
                container.style.opacity = "1";
            }
        });
    };

    // Listen for any changes in AI configuration
    document.querySelectorAll('select, input[type="range"]').forEach(el => {
        el.addEventListener('input', () => {
            updateSliderLabels();
            checkTurnStatus();
        });
    });

    const makeComputerMove = async () => {
        if (game.game_over()) return;

        const isWhiteTurn = game.turn() === 'w';
        const currentAlgo = isWhiteTurn ? document.getElementById('white-algo').value : document.getElementById('black-algo').value;

        // EXIT if the current side is set to Human (none)
        if (currentAlgo === 'none') return;

        // Check if it's the AI's legitimate turn or Battle Mode is active
        const isAiTurn = (isWhiteTurn && userColor === 'b') || (!isWhiteTurn && userColor === 'w');
        if (!isAiBattle && !isAiTurn) return;

        const val = isWhiteTurn ? document.getElementById('white-slider').value : document.getElementById('black-slider').value;

        try {
            const aiName = currentAlgo === 'mcts' ? 'MCTS' : 'Alpha-Beta';
            updateStatus(`${aiName} (${isWhiteTurn ? 'White' : 'Black'}) is thinking...`, "warning");

            const response = await fetch('/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fen: game.fen(),
                    algo: currentAlgo,
                    value: val
                })
            });

            const data = await response.json();
            if (!data || !data.move) return;

            game.move({ from: data.move.substring(0, 2), to: data.move.substring(2, 4), promotion: 'q' });
            board.position(game.fen());
            moveCount++;
            checkTurnStatus();

            // Recursion for AI Battle mode
            if (isAiBattle && !game.game_over()) {
                window.setTimeout(makeComputerMove, 600);
            }
        } catch (error) {
            console.error("AI Error:", error);
            isAiBattle = false;
            updateStatus("Connection Lost", "error");
        }
    };

    // RESTART: Reset game and logic
    document.getElementById('btn-restart').addEventListener('click', () => {
        isAiBattle = false;
        game.reset();
        board.start();
        userColor = 'w';
        moveCount = 1;
        checkTurnStatus();
        document.getElementById('btn-ai-vs-ai').style.display = 'inline-block';
        document.getElementById('btn-stop').style.display = 'none';
    });

    // SWITCH SIDES: Only flip board and update perspective. DO NOT call AI.
    document.getElementById('btn-switch').addEventListener('click', () => {
        board.flip();
        userColor = (userColor === 'w') ? 'b' : 'w';
        checkTurnStatus();
        // Automatic AI call removed to prevent unrequested moves
    });

    // AI vs AI Battle Mode
    document.getElementById('btn-ai-vs-ai').addEventListener('click', function() {
        if (document.getElementById('white-algo').value === 'none' ||
            document.getElementById('black-algo').value === 'none') {
            alert("Battle Mode requires AI selected for both sides!");
            return;
        }
        isAiBattle = true;
        this.style.display = 'none';
        document.getElementById('btn-stop').style.display = 'inline-block';
        makeComputerMove();
    });

    document.getElementById('btn-stop').addEventListener('click', function() {
        isAiBattle = false;
        this.style.display = 'none';
        document.getElementById('btn-ai-vs-ai').style.display = 'inline-block';
    });

    // Status Checker: Show current turn and selected engine info
    const checkTurnStatus = () => {
        if (game.game_over()) {
            handleGameOver();
            return;
        }

        const isWhiteTurn = game.turn() === 'w';
        const currentAlgo = isWhiteTurn ? document.getElementById('white-algo').value : document.getElementById('black-algo').value;
        const isUserTurn = game.turn() === userColor;

        if (currentAlgo === 'none' || isUserTurn) {
            updateStatus(`Your Turn (${isWhiteTurn ? 'White' : 'Black'})`, "success");
        } else {
            const aiName = currentAlgo === 'mcts' ? 'MCTS' : 'Alpha-Beta';
            updateStatus(`${aiName}'s Turn (${isWhiteTurn ? 'White' : 'Black'})`, "warning");
        }
    };

    const updateStatus = (text, type) => {
        const statusText = document.getElementById('status-text');
        const statusDot = document.querySelector('.status-dot');
        if (!statusText || !statusDot) return;
        statusText.textContent = text;
        const colors = { success: '#22c55e', warning: '#f59e0b', error: '#ef4444' };
        statusDot.style.backgroundColor = colors[type];
    };

    const handleGameOver = () => {
        let message = "Game Over";
        if (game.in_checkmate()) {
            const winner = game.turn() === 'w' ? "Black" : "White";
            message = `CHECKMATE! ${winner} Wins!`;
        } else if (game.in_draw()) {
            message = "Draw Game!";
        }
        updateStatus(message, "error");
        alert(message);
    };

    const boardConfig = {
        draggable: true,
        position: 'start',
        onDragStart: (source, piece) => {
            if (game.game_over()) return false;
            const isWhiteTurn = game.turn() === 'w';
            const currentAlgo = isWhiteTurn ? document.getElementById('white-algo').value : document.getElementById('black-algo').value;
            // Prevent dragging if it's AI's turn
            if (currentAlgo !== 'none' && game.turn() !== userColor) return false;
        },
        onDrop: (source, target) => {
            const move = game.move({ from: source, to: target, promotion: 'q' });
            if (move === null) return 'snapback';
            moveCount++;
            checkTurnStatus();
            window.setTimeout(makeComputerMove, 250);
        },
        onSnapEnd: () => board.position(game.fen()),
        pieceTheme: '/static/img/chesspieces/wikipedia/{piece}.png',
    };

    board = Chessboard('board', boardConfig);
    updateSliderLabels();
    checkTurnStatus();
});