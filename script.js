// Wait for the DOM to be fully loaded before executing code
document.addEventListener('DOMContentLoaded', () => {
    let board = null; // Initialize the chessboard
    const game = new Chess(); // Create new Chess.js game instance
    const moveHistory = document.getElementById('move-history'); // Get move history container
    let moveCount = 1; // Initialize the move count
    let userColor = 'w'; // Initialize the user's color as white
    let botIsRunning = false;

    // Function to make a move for the computer via API
    const makeRandomMove = async () => {
        if (game.game_over()) {
            alert("Checkmate!");
            return 1;
        }

        try {
            const response = await fetch('http://127.0.0.1:5003/move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    fen: game.fen()
                })
            });

            const data = await response.json();

            // ❗ kiểm tra dữ liệu trả về
            if (!data || !data.move) {
                console.error("Invalid API response:", data);
                return -1;
            }

            console.log("API move:", data.move);

            // ✅ convert UCI → object cho chess.js
            const moveObj = {
                from: data.move.substring(0, 2),
                to: data.move.substring(2, 4),
                promotion: 'q'
            };

            const move = game.move(moveObj);

            // ❗ tránh lỗi null.san
            if (move === null) {
                console.error("Invalid move from API:", data.move);
                console.log("Current FEN:", game.fen());
                return -2;
            }

            board.position(game.fen());
            recordMove(move.san, moveCount);
            moveCount++;
            return 0;

        } catch (error) {
            console.error("API error:", error);
            return -3;
        }
    };

    // Function to record and display a move in the move history
    const recordMove = (move, count) => {
        const formattedMove = count % 2 === 1 ? `${Math.ceil(count / 2)}. ${move}` : `${move} -`;
        moveHistory.textContent += formattedMove + ' ';
        moveHistory.scrollTop = moveHistory.scrollHeight; // Auto-scroll to the latest move
    };

    // Function to handle the start of a drag position
    const onDragStart = (source, piece) => {
        // Allow the user to drag only their own pieces based on color
        return !game.game_over() && piece.search(userColor) === 0;
    };

    // Function to handle a piece drop on the board
    const onDrop = (source, target) => {
        const move = game.move({
            from: source,
            to: target,
            promotion: 'q',
        });

        if (move === null) return 'snapback';

        window.setTimeout(makeRandomMove, 250);
        recordMove(move.san, moveCount); // Record and display the move with move count
        moveCount++;
    };

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
        moveSpeed: 'fast',
        snapBackSpeed: 500,
        snapSpeed: 100,
    };

    // Initialize the chessboard
    board = Chessboard('board', boardConfig);

    // Event listener for the "Play Again" button
    document.querySelector('.play-again').addEventListener('click', () => {
        game.reset();
        board.start();
        moveHistory.textContent = '';
        moveCount = 1;
        userColor = 'w';
    });

    // Event listener for the "Set Position" button
    document.querySelector('.set-pos').addEventListener('click', () => {
        const fen = prompt("Enter the FEN notation for the desired position!");
        if (fen !== null) {
            if (game.load(fen)) {
                board.position(fen);
                moveHistory.textContent = '';
                moveCount = 1;
                userColor = 'w';
            } else {
                alert("Invalid FEN notation. Please try again.");
            }
        }
    });

    // Event listener for the "Flip Board" button
    document.querySelector('.flip-board').addEventListener('click', () => {
        board.flip();
        makeRandomMove();
        // Toggle user's color after flipping the board
        userColor = userColor === 'w' ? 'b' : 'w';
    });

  const botVBot = async () => {
    if (botIsRunning) {return;}

    botIsRunning = true;
    while (botIsRunning) {
      const result = await makeRandomMove();
      if (result != 0) {
        botIsRunning = false;
        break;
      }

      // delay to see the moves being made
      await new Promise(resolve => setTimeout(resolve, 300));
    }
  }

  const botBtn = document.querySelector('.bot-v-bot');
  botBtn.addEventListener('click', () => {
    if (botIsRunning) {
      botIsRunning = false;
      botBtn.textContent = "Start Bot vs Bot";
    } else {
      botBtn.textContent = "Stop Bot vs Bot";
      botVBot();
    }
  });

});

