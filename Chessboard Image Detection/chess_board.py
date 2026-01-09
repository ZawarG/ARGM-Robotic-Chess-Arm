from chess_square import ChessSquare

class ChessBoard:
    def __init__(self, coord):
        self.coord = coord # list of all positions of each square in board

        # vision layer
        self.squares = [[None for _ in range(8)] for _ in range(8)] # create list of chesssquare objects storing images
        
        # current occupancy state
        self.curr_occ = [[False for _ in range(8)] for _ in range(8)] # create list of characters storing the state of the square, e.g. 'P' for white pawn

        # previous occupancy state
        self.prev_occ = [[False for _ in range(8)] for _ in range(8)]

        # FEN related fields
        self.currmov = "w" # starts with white and alternates at each turn
        self.castle = "KQkq" # possibility to castle
        self.enpass = "-" # possibility for en passant
        self.halfmoves = 0 # moves since last capture / pawn advance
        self.fullmoves = 1 # number of full moves, incremented after black's turn

        # initialize start positions and vision squares
        self.initStartPos()
    
    # update images, used for processing (checking if the space is empty)
    def updateSquares(self, img):
        for row in range(8):
            for col in range(8):
                top_left = self.coord[row, col]
                bottom_right = self.coord[row+1, col+1]

                cropped_square = img[int(top_left[1]):int(bottom_right[1]), int(top_left[0]):int(bottom_right[0])]
                
                if self.squares[row][col] is None:
                    square_object = ChessSquare(cropped_square, row, col)
                    self.squares[row][col] = square_object
                else:
                    self.squares[row][col].image = cropped_square


    def updateOccupancyCheckChanged(self):
        self.curr_occ = [[False for _ in range(8)] for _ in range(8)]
        changed = []
        
        for row in range(8):
            for col in range(8):
                self.curr_occ[row][col] = self.squares[row][col].is_occupied()

                if self.curr_occ[row][col] != self.prev_occupancy[row][col]:
                    changed.append((row,col))

        self.prev_occ = self.curr_occ
        return changed




    # apply initial chess state
    def initStartPos(self):
        for col in range(8):
            for row in [0,1,6,7]:
                self.prev_occ[row][col] = True
        # initial_row = ['r','n','b','q','k','b','n','r']

        # for col in range(8):
        #     self.state[0][col] = initial_row[col]
        #     self.state[1][col] = 'p'
        #     self.state[6][col] = 'P'
        #     self.state[7][col] = initial_row[col].upper()

        # def boardToFEN(self):
        # fen = ""

        # # board position values in fenstring
        # for i in range(8):
        #     empty_count = 0
        #     for j in range(8):
        #         char = self.state[i][j]
                
        #         if char is None:
        #             empty_count+=1
        #         else:
        #             if empty_count > 0:
        #                 fen+=str(empty_count)
        #                 empty_count = 0
        #             fen+=str(char)

        #     if empty_count > 0:
        #         fen+=str(empty_count)

        #     if i!=7:
        #         fen+="/"
        
        # # other values in fenstring
        # fen += (self.currmov + " " + 
        #         self.castle + " " + 
        #         self.enpass + " " + 
        #         str(self.halfmoves) + " " + 
        #         str(self.fullmoves))

        # return fen