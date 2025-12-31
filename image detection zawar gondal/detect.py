import cv2
import numpy as np

# Read the image
image_path = r"C:\Users\zawar\OneDrive\Desktop\ARGM\ARGM-Robotic-Chess-Arm\image detection zawar gondal\test.jpg"
img = cv2.imread(image_path)

lwr = np.array([0, 0, 143])
upr = np.array([179, 61, 252])
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
msk = cv2.inRange(hsv, lwr, upr)

krn = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 30))
dlt = cv2.dilate(msk, krn, iterations=5)

res = 255 - cv2.bitwise_and(dlt, msk)

res = np.uint8(res)

ret, corners = cv2.findChessboardCorners(res, (7, 7),
                                         flags=cv2.CALIB_CB_ADAPTIVE_THRESH +
                                               cv2.CALIB_CB_FAST_CHECK +
                                               cv2.CALIB_CB_NORMALIZE_IMAGE)
if ret:
    fnl = cv2.drawChessboardCorners(img, (7, 7), corners, ret)
    cv2.imshow("Chessboard with Corners", fnl)
    cv2.waitKey(0)

    inter_x_dist = corners[1].tolist()[0][0]-corners[0].tolist()[0][0]
    inter_y_dist = corners[8].tolist()[0][1]-corners[0].tolist()[0][1]

else:
    print("No Checkerboard Found")


"""from this point on it should not be too complicated to finish off the code. All you do is crop the images in
each square, and check if that square is empty or not. You can do this by checking for how many pixels are not the dominant
pixel in that square. This shouldnt be too hard. maybe you could even check using noise or something idk really. But afterwards, save the 8x8 board as a
array of True/False or 1/0s. In the initial state, make all pawns 1, knights 2, bishops 3, rook 4 and king 5 queen 6. Then to differentitate between one side and the other
what you can do is assign w to the white pieces so 1w is a white pawn in that square. Then when a piece moves from one square to another you check which became empty and which is now filled
so then what happens is you replace that number there. So if 2b moves i.e a black knight then the place it was before becomes empty and the place it moves to now has 2b value. The only thing you have to watch
out for is taking pieces, for that youll most likely have to account for whos turn it is. 
If you can figure out how to convert the array into a FENstring. Then we have fully functional chess engine.
"""
