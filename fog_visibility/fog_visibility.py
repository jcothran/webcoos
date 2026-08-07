import cv2
import numpy as np
import os
import time
import argparse

# Configurations via environment variables for flexibility
THRESHOLD = float(os.getenv("FOG_THRESHOLD", "15.0"))

def analyze_fog(image_path):
    # Load image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: Unable to load image {image_path}")
        return None

    # Focus on the top half of the image where atmospheric fog is most visible
    h, w = img.shape
    roi = img[0:int(h/2), 0:w]

    # Calculate gradients along X and Y using Sobel filters
    sobelx = cv2.Sobel(roi, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(roi, cv2.CV_64F, 0, 1, ksize=3)
    
    # Compute magnitude of gradients
    magnitude = np.sqrt(sobelx**2 + sobely**2)
    
    # Average edge density score
    edge_score = np.mean(magnitude)
    
    # Determine visibility status
    status = "FOG DETECTED" if edge_score < THRESHOLD else "CLEAR VISIBILITY"
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Image: {image_path} | Edge Score: {edge_score:.2f} | Status: {status}")
    return status

if __name__ == "__main__":
    # Setup argument parsing for a single image pass
    parser = argparse.ArgumentParser(description="Analyze an image for fog using edge density.")
    parser.add_argument("image_path", help="Path to the image file to analyze")
    args = parser.parse_args()

    # Validate file existence before attempting to process
    if not os.path.exists(args.image_path):
        print(f"Error: The file '{args.image_path}' does not exist.")
    else:
        analyze_fog(args.image_path)
