
import cv2
import numpy as np

img = np.zeros((100, 100, 3), dtype=np.uint8)
img[:] = [255, 0, 0] # Blue
cv2.imwrite('input.jpg', img)
print("Created input.jpg")
