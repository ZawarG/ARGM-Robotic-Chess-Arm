import cv2
import numpy as np

#  (\(\
# ( -.-)
# o_(")(")
# This file holds stateless helper functions for square occupancy:
# preparing a square's HSV image, 
# scoring how far it deviates from its empty reference, 
# and the image-subtraction diff used to confirm captures

# Square occupancy
def adjustSquare(img, border_ratio=0.1):
    # Crop
    height, width = img.shape[:2]
    b_top_height = int(height * border_ratio)
    b_bot_height = int(height * border_ratio * 4) # Crop bottom extra to account for how piece tops overlapping due camera angle
    b_width = int(width * border_ratio)
    img = img[b_top_height:height-b_bot_height, b_width:width-b_width]

    # Detect average brightness and std
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    return hsv

# Per-pixel Euclidean z-score of an HSV square vs its (exposure-adjusted) empty reference profile
# High where a piece deviates from the learned empty colour
# Shared by occupancy detection and the debug overlays so they stay in sync
def computeFillZ(square, profile):
    # Adjust the empty-square reference for exposure drift since calibration
    hsv_offset = profile['curr_hsv'] - profile['avg_hsv']
    avg_sq = profile['avg_sq'] + hsv_offset

    # Per-channel z-scores, then 3D Euclidean distance across H, S, V
    z_channels = np.abs(square.astype(np.float32) - avg_sq) / (profile['std_sq'] + 1)
    return np.sqrt(np.sum(np.square(z_channels), axis=2))

def checkOccupancy(square, profile, name, FILL_THRESH = 0.3):
    start_frame_bright = profile['avg_hsv']
    curr_frame_bright = profile['curr_hsv']

    # Per-pixel deviation from the empty-square reference
    fill_z = computeFillZ(square, profile)

    # Detect contour area and shape
    fill_ratio = detectContourArea(fill_z, square)

    # Create threshold for fill area
    hsv_ratio = curr_frame_bright/start_frame_bright
    adaptive_fill_thresh = FILL_THRESH*hsv_ratio

    return fill_ratio > adaptive_fill_thresh

# Per-pixel HSV difference between two HSV squares (same size), returned as a
# single-channel magnitude map. Used for image subtraction (e.g. confirming a
# capture, which occupancy alone can't see: opponent piece -> mover's piece).
#   - Hue is treated circularly (OpenCV hue is 0-179 and wraps) and weighted by
#     saturation, so low-saturation pixels (white/black pieces, where hue is just
#     noise) don't dominate the score.
#   - Value gets the lighting offset subtracted so exposure drift between the
#     reference frame and now doesn't register as change.
def hsvDifferenceMap(cur_hsv, ref_hsv, v_offset=0.0):
    cur = cur_hsv.astype(np.float32)
    ref = ref_hsv.astype(np.float32)

    dh = np.abs(cur[:, :, 0] - ref[:, :, 0])
    dh = np.minimum(dh, 180.0 - dh)              # hue wraps at 180
    ds = np.abs(cur[:, :, 1] - ref[:, :, 1])
    dv = np.abs((cur[:, :, 2] - v_offset) - ref[:, :, 2])

    # Weight hue by how saturated the pixels are (avg of the two frames, 0-1),
    # since hue is meaningless when saturation is low
    sat_weight = np.minimum(cur[:, :, 1], ref[:, :, 1]) / 255.0

    return dh * sat_weight + ds + dv

def detectContourArea(z, square, show=False):
    mask = (z > 3.25).astype(np.uint8) * 255
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel)
    kernel2 = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel2)

    fill_area = np.count_nonzero(mask)
    fill_ratio = fill_area / mask.size

    # weight = gaussian(center)
    # weighted_fill = np.sum(mask * weight)

    if show:
        bgr_img = cv2.cvtColor(square, cv2.COLOR_HSV2BGR)
        overlay = bgr_img.copy()
        overlay[mask > 0] = (0, 0, 255)
        display = cv2.addWeighted(bgr_img, 0.7, overlay, 0.3, 0)

        cv2.putText(display, f"Area: {fill_area}", (5, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow("Fill Area", display)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return fill_ratio
