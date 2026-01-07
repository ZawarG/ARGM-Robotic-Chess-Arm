class ChessBoard:
    def __init__(self, coord):
        self.coord = coord # list of all positions of each square in board
        self.currmov = " w" # starts with white and alternates at each turn
        self.halfmoves = 0 # moves since last capture / pawn advance
        self.fullmoves = 1 # number of full moves, incremented after black's turn

        self.castle = " KQkq"
        self.enpass = " - "
        
        self.board = [[] for _ in range(8)] # create list of square object storing images and coordinates

    def boardToFEN(self):
        fen = ""

        # board position values in fenstring
        for i in range(8):
            empty_count = 0
            for j in range(8):
                char = self.board[i][j].getFENValue()
                
                if char == 0:
                    empty_count+=1
                    print("running", empty_count)
                else:
                    if empty_count > 0:
                        fen+=str(empty_count)
                        empty_count = 0
                    fen+=str(char)

                if empty_count == 8:
                    fen+=str(empty_count)

            if i!=7:
                fen+="/"
        
        # other values in fenstring
        fen = fen + self.currmov + self.castle + self.enpass + str(self.halfmoves) + " " + str(self.fullmoves)

        return fen
    
    # update images, used for processing (checking if the space is empty)
    def updateBoard(self, img):
        for row in range(8):
            for col in range(8):
                top_left = self.coord[row, col]
                bottom_right = self.coord[row+1, col+1]

                cropped_square = img[int(top_left[1]):int(bottom_right[1]), int(top_left[0]):int(bottom_right[0])]
                square_object = ChessSquare(cropped_square, row, col)

                self.board[row].append(square_object)

class ChessSquare:
    def __init__(self, image, row, col):
        self.image = image
        self.row = row
        self.col = col

        # initialize piece info
        self.occupied = False
        self.piece = None
        self.color = None # 1 for them, 0 for us

    def getFENValue(self):
        if not self.occupied:
            return 0
        
        if self.colour == 0:
            return self.piece.upper()
        else:
            return self.piece