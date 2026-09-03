import cv2
from src.logic.chess_board import ChessBoard
import src.ui.debugger as debugger

#  (\(\
# ( -.-)
# o_(")(")
# Shared interactive controls for the live windows (both the camera path in main() and the recorded-video path in testCode())
# Keeps the keyboard handling and the display/overlay loop in one place so both stay in sync.

# Handles a single keypress for the live loop.
# Returns the (possibly updated) paused flag and whether the user asked to quit.
def handleKeyInput(key, game, img, paused):
    # While awaiting a promotion, q/r/b/n select the piece and Enter confirms the choice
    # These are gated here so 'q' means Queen instead of Quit.
    if game.started and game.isAwaitingPromotion():
        if key in (ord('q'), ord('r'), ord('b'), ord('n')):
            game.selectPromotion(chr(key))
        elif key in (13, 10):  # Enter (CR / LF)
            game.confirmPromotion()

    elif key == ord('s') and not game.started:  # 'S' calibrates + starts the game
        game.beginGame(img)  # uses the current frame (pieces in place)
        print("Game started")

    elif key == ord(' '):  # Spacebar toggles pause/play
        paused = not paused
        print("Status:", "PAUSED" if paused else "PLAYING")

    elif key == ord('d') and game.started:  # 'D' shows per-square diff heatmap
        debugger.displayDifferences(game.vision, ChessBoard.CAPTURE_DIFF_THRESHOLD)

    elif key == ord('q'):  # 'Q' quits the stream
        return paused, True

    return paused, False

# Shared display/update loop used by both run paths.
#   cap         - a cv2.VideoCapture (camera or video file)
#   game        - a ChessBoard (already localized but not yet started)
#   M           - perspective matrix, for the setup-phase warp overlay
#   window_name - title of OpenCV window
# Runs until game ends or user quits, then returns winner (or None).
def runGameLoop(cap, game, M, window_name="Live Chess Matrix Tracker"):
    paused = False
    winner = None

    while True:
        # If not paused, capture new frame
        if not paused:
            ret, img = cap.read()
            if not ret:
                break

        if not game.started:
            # Setup phase: show live warped feed so the user can place pieces
            # Press 'S' to calibrate from this frame and start
            live_display = debugger.drawSetupOverlay(img, M)
        else:
            # Game phase: update engine, draw the occupancy overlay
            if not paused:
                winner = game.update(img)
                if winner is not None:
                    print(winner)
                    break

            live_display = debugger.drawOccupancyOverlay(game.vision)

            # Promotion prompt: vision saw a pawn promote but can't tell into what
            if game.isAwaitingPromotion():
                live_display = debugger.drawPromotionOverlay(live_display, game)

        # Show live video window
        cv2.imshow(window_name, live_display)

        # Intercept keyboard keys
        key = cv2.waitKey(1) & 0xFF
        paused, quit_requested = handleKeyInput(key, game, img, paused)
        if quit_requested:
            break

    return winner
