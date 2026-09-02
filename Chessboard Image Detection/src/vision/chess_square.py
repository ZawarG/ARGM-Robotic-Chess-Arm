import numpy as np
import src.vision.utils as utils

#  (\(\
# ( -.-)
# o_(")(")
# Each square in the chess board is its own object.
# This class holds information related to a single square in the chess board
# Specifically, each square's occupancy is checked

class ChessSquare: # responsibile for vision aspect
    def __init__(self, image, row, col, file, rank):
        self.image = image

        self.coord = (row, col)
        file_int = ord(file) - 96
        self.name = f"{file}{rank}"
        self.is_light_square = (file_int+rank) % 2 # 0 for dark, 1 for light

        # initialize piece info
        self.occupancy = True       # Initialized in board_vision

        # Reference image from the last confirmed board state, used for
        # image subtraction (e.g. to confirm a capture that occupancy can't see)
        self.reference_image = image

    def setReference(self, value):
        self.base_profile = value

    def setOccupancy(self, value):
        self.occupancy = value

    def updateOccupancy(self, image, profile):
        self.image = image
        self.occupancy = utils.checkOccupancy(self.image, profile, self.name)

    def getOccupancy(self):
        return self.occupancy

    # Freeze the current image as the reference to diff future frames against
    # Call after a move is confirmed so "previous stable frame" stays one move behind
    def snapshotReference(self):
        self.reference_image = self.image.copy() if self.image is not None else None

    # Per-pixel HSV difference map vs the reference (None if not comparable).
    # v_offset compensates exposure drift between the reference frame and now.
    def differenceMap(self, v_offset=0.0):
        if self.reference_image is None or self.image is None:
            return None
        if self.reference_image.shape != self.image.shape:
            return None
        return utils.hsvDifferenceMap(self.image, self.reference_image, v_offset)

    # Scalar diff score: mean of the per-pixel HSV difference map.
    def difference(self, v_offset=0.0):
        diff_map = self.differenceMap(v_offset)
        return 0.0 if diff_map is None else float(np.mean(diff_map))
