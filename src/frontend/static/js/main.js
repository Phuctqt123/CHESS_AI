// Wait for the DOM to be fully loaded before executing code
document.addEventListener('DOMContentLoaded', () => {
    let board = null; // Initialize the chessboard
    const game = new Chess(); // Create new Chess.js game instance
    const moveHistory = document.getElementById('move-history'); // Get move history container
    let moveCount = 1; // Initialize the move count
    let userColor = 'w'; // Initialize the user's color as white
    let pendingMove = null; // Store pending promotion move
    let botIsRunning = false;
    const promotionModal = document.getElementById('promotion-modal');
    const depthSlider = document.getElementById('depth-slider');
    const depthValueDisplay = document.getElementById('depth-value');

    // Update depth display when slider moves
    if (depthSlider && depthValueDisplay) {
        depthSlider.addEventListener('input', () => {
            depthValueDisplay.textContent = depthSlider.value;
        });
    }

    // Function to make a move for the computer via API
    const makeComputerMove = async () => {
        if (game.game_over()) {
            handleGameOver();
            return 1;
        }

        try {
            const currentDepth = depthSlider ? parseInt(depthSlider.value) : 3;
            const response = await fetch('/move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    fen: game.fen(),
                    depth: currentDepth
                })
            });

            const data = await response.json();

            if (!data || !data.move) {
                console.error("Invalid API response:", data);
                updateStatus("AI Error", "error");
                return -1;
            }

            const moveObj = {
                from: data.move.substring(0, 2),
                to: data.move.substring(2, 4),
                promotion: data.move.length > 4 ? data.move.substring(4, 5) : 'q'
            };

            const move = game.move(moveObj);

            if (move === null) {
                console.error("Invalid move from API:", data.move);
                return -2;
            }

            board.position(game.fen());
            recordMove(move.san, moveCount);
            moveCount++;
            
            checkTurnStatus();
            return 0;

        } catch (error) {
            console.error("API error:", error);
            updateStatus("Connection Lost", "error");
            return -3;
        }
    };

    // Function to record and display a move in the move history
    const recordMove = (move, count) => {
        if (count === 1) {
            moveHistory.innerHTML = ''; // Clear placeholder on first move
        }

        const isWhite = count % 2 === 1;
        const moveNumber = Math.ceil(count / 2);

        if (isWhite) {
            // Create a new row for the move number and white's move
            const moveRow = document.createElement('div');
            moveRow.className = 'move-row';
            moveRow.innerHTML = `
                <span class="move-number">${moveNumber}.</span>
                <span class="white-move">${move}</span>
            `;
            moveHistory.appendChild(moveRow);
        } else {
            // Find the last row and append black's move to it
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
        
        const isUserTurn = game.turn() === userColor;
        const turnText = isUserTurn ? `Your Turn (${userColor === 'w' ? 'White' : 'Black'})` : "AI's Turn (Thinking)";
        updateStatus(turnText, isUserTurn ? "success" : "warning");
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
        if (game.in_checkmate()) status = "Checkmate!";
        else if (game.in_draw()) status = "Draw!";
        updateStatus(status, "error");
        alert(status);
    };

    // Function to handle the start of a drag position
    const onDragStart = (source, piece) => {
        if (game.game_over()) return false;
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
        // Exit if it's not the user's turn
        if (game.turn() !== userColor) return;

        // Get list of possible moves for this square
        const moves = game.moves({
            square: square,
            verbose: true
        });

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
    // --- End Highlighting Logic ---

    // Function to handle a piece drop on the board

    // Function to handle a piece drop on the board
    const onDrop = (source, target) => {
        removeHighlights();
        
        // Check if move is legal
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
            return 'snapback';
        }

        const move = game.move({
            from: source,
            to: target,
            promotion: 'q',
        });

        recordMove(move.san, moveCount);
        moveCount++;
        
        checkTurnStatus(); // Update to "AI's Turn"
        window.setTimeout(makeComputerMove, 250);
    };

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
        const move = game.move({
            from: source,
            to: target,
            promotion: piece
        });

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

    // Function to handle the end of a piece snap animation
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
        // Updated path for pieces
        pieceTheme: '/static/img/chesspieces/wikipedia/{piece}.png',
        moveSpeed: 'fast',
    };

    // Initialize the chessboard
    board = Chessboard('board', boardConfig);

    // Event listener for the "Play Again" button
    document.querySelector('.play-again').addEventListener('click', () => {
        game.reset();
        board.start();
        moveHistory.innerHTML = '<div class="history-placeholder">Waiting for the first move...</div>';
        moveCount = 1;
        userColor = 'w';
        pendingMove = null;
        promotionModal.style.display = 'none';
        checkTurnStatus();
        
        // Stop bot if it was running
        if (botIsRunning) {
            botIsRunning = false;
            const botBtn = document.querySelector('.bot-v-bot');
            if (botBtn) botBtn.innerHTML = '<i class="fas fa-robot"></i> Bot vs Bot';
        }
    });



    // Event listener for the "Flip Board" button
    document.querySelector('.flip-board').addEventListener('click', () => {
        board.flip();
        userColor = userColor === 'w' ? 'b' : 'w';
        
        checkTurnStatus();
        
        // If it's now the computer's turn after flipping
        if (game.turn() !== userColor) {
            makeComputerMove();
        }
    });

    const botVBot = async () => {
        if (botIsRunning) return;

        botIsRunning = true;
        const botBtn = document.querySelector('.bot-v-bot');
        
        while (botIsRunning) {
            const result = await makeComputerMove();
            if (result !== 0) {
                botIsRunning = false;
                botBtn.innerHTML = '<i class="fas fa-robot"></i> Bot vs Bot';
                break;
            }

            // delay to see the moves being made
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
