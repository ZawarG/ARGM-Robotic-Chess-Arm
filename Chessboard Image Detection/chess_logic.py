class ChessBoard:
    def __init__(self, coord):
        self.coord = coord # list of all positions of each square in board

        # vision layer
        self.squares = [[None for _ in range(8)] for _ in range(8)] # create list of chesssquare objects storing images
        
        # logical game state
        self.state = [[None for _ in range(8)] for _ in range(8)] # create list of characters storing the state of the square, e.g. 'P' for white pawn

        # previous snapshot
        self.prev = [[None for _ in range(8)] for _ in range(8)]

        # FEN related fields
        self.currmov = "w" # starts with white and alternates at each turn
        self.castle = "KQkq" # possibility to castle
        self.enpass = "-" # possibility for en passant
        self.halfmoves = 0 # moves since last capture / pawn advance
        self.fullmoves = 1 # number of full moves, incremented after black's turn

        # initialize start positions and vision squares
        self.initStartPos()

    def boardToFEN(self):
        fen = ""

        # board position values in fenstring
        for i in range(8):
            empty_count = 0
            for j in range(8):
                char = self.state[i][j]
                
                if char is None:
                    empty_count+=1
                else:
                    if empty_count > 0:
                        fen+=str(empty_count)
                        empty_count = 0
                    fen+=str(char)

            if empty_count > 0:
                fen+=str(empty_count)

            if i!=7:
                fen+="/"
        
        # other values in fenstring
        fen += (self.currmov + " " + 
                self.castle + " " + 
                self.enpass + " " + 
                str(self.halfmoves) + " " + 
                str(self.fullmoves))

        return fen
    
    # update images, used for processing (checking if the space is empty)
    def updateSquares(self, img):
        for row in range(8):
            for col in range(8):
                top_left = self.coord[row, col]
                bottom_right = self.coord[row+1, col+1]

                cropped_square = img[int(top_left[1]):int(bottom_right[1]), int(top_left[0]):int(bottom_right[0])]
                square_object = ChessSquare(cropped_square, row, col)

                self.squares[row][col] = square_object

    # apply initial chess state
    def initStartPos(self):
        initial_row = ['r','n','b','q','k','b','n','r']

        for col in range(8):
            self.state[0][col] = initial_row[col]
            self.state[1][col] = 'p'
            self.state[6][col] = 'P'
            self.state[7][col] = initial_row[col].upper()

class ChessSquare:
    def __init__(self, image, row, col):
        self.image = image
        self.row = row
        self.col = col

        # initialize piece info
        self.occupied = False # from image analysis

    def getFENValue(self):
        if not self.occupied:
            return 0
        
        if self.colour == 0:
            return self.piece.upper()
        else:
            return self.piece