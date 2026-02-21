
import cv2
import numpy as np
import os

def create_stereo_pair(output_dir="images"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    width, height = 800, 600
    
    # 1. Create a background with random noise for texture
    np.random.seed(42)
    background = np.random.randint(0, 255, (height, width), dtype=np.uint8)
    
    # 2. Create base image (left view)
    img_left = cv2.cvtColor(background, cv2.COLOR_GRAY2BGR)
    
    # Add some distinct shapes
    # A red square
    cv2.rectangle(img_left, (200, 200), (400, 400), (0, 0, 255), -1)
    # A green circle
    cv2.circle(img_left, (600, 300), 50, (0, 255, 0), -1)
    # A blue text
    cv2.putText(img_left, "SfM Test", (300, 500), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 4)

    # 3. Create right image (shift everything slightly to left = camera moved right)
    shift = 20 # pixels
    M = np.float32([[1, 0, -shift], [0, 1, 0]])
    img_right = cv2.warpAffine(img_left, M, (width, height))
    
    # Fill the gap on the right with noise
    noise_strip = np.random.randint(0, 255, (height, shift, 3), dtype=np.uint8)
    img_right[:, -shift:] = noise_strip

    # Save images
    cv2.imwrite(os.path.join(output_dir, "left.png"), img_left)
    cv2.imwrite(os.path.join(output_dir, "right.png"), img_right)
    
    print(f"Created stereo pair in {output_dir}: left.png, right.png")

if __name__ == "__main__":
    create_stereo_pair()
