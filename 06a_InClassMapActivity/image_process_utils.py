import cv2
import numpy as np
        
# Gets the color at an x,y coordinate in an image
def get_color_at_point(x, y, img_path="captured_image.jpg"):
    img = cv2.imread(img_path)  # BGR format

    # Get exact pixel color
    color = img[y, x]   # (B, G, R)
    print("Exact pixel color (BGR):", color)

    return color


# Gets the average color at an x,y coordinate in an image
def get_avg_color_at_point(x, y, radius=5, img_path="captured_image.jpg"):
    img = cv2.imread(img_path)  # BGR format
    # Get average color in a region around the coordinate
    roi = img[y-radius:y+radius+1, x-radius:x+radius+1]
    avg_color = roi.mean(axis=(0,1))
    print("Average color around point (BGR):", avg_color)
    
    return avg_color