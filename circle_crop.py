import cv2
import numpy as np
import os
import glob
from pathlib import Path

def create_circular_mask(h, w, center=None, radius=None):
    """Function to create a circular mask."""
    if center is None:
        center = (int(w/2), int(h/2))
    if radius is None:
        radius = min(center[0], center[1], w-center[0], h-center[1])
    
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)
    
    mask = dist_from_center <= radius
    return mask

def crop_circle_from_image(image_path, output_path):
    """Crop the largest possible circular area from the center of the image and save it."""
    # Load image
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Could not load image: {image_path}")
        return False
    
    h, w = img.shape[:2]
    
    # Calculate center point
    center_x, center_y = w // 2, h // 2
    
    # Calculate maximum radius (largest size that doesn't touch the image boundary)
    radius = min(center_x, center_y, w - center_x, h - center_y)
    
    # Create circular mask
    mask = create_circular_mask(h, w, center=(center_x, center_y), radius=radius)
    
    # Apply mask
    if len(img.shape) == 3:  # Color image
        masked_img = img.copy()
        masked_img[~mask] = 0  # Set area outside the mask to black
    else:  # Grayscale image
        masked_img = img.copy()
        masked_img[~mask] = 0
    
    # Crop only the circular area (bounding box)
    crop_x1 = center_x - radius
    crop_y1 = center_y - radius
    crop_x2 = center_x + radius
    crop_y2 = center_y + radius
    
    cropped_img = masked_img[crop_y1:crop_y2, crop_x1:crop_x2]
    
    # Save
    cv2.imwrite(output_path, cropped_img)
    return True

def process_all_images():
    """Process all images in the 'img' folder."""
    # Set input and output paths
    input_dir = "img"
    output_dir = "img/circle"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .tif files
    image_files = glob.glob(os.path.join(input_dir, "*.tif"))
    
    if not image_files:
        print("No images to process.")
        return
    
    print(f"Processing {len(image_files)} images in total...")
    
    processed_count = 0
    failed_count = 0
    
    for i, image_path in enumerate(image_files, 1):
        # Extract filename
        filename = os.path.basename(image_path)
        output_path = os.path.join(output_dir, filename)
        
        # Process image
        if crop_circle_from_image(image_path, output_path):
            processed_count += 1
            if i % 50 == 0:  # Print progress every 50 images
                print(f"Progress: {i}/{len(image_files)} ({i/len(image_files)*100:.1f}%)")
        else:
            failed_count += 1
            print(f"Processing failed: {filename}")
    
    print(f"\nProcessing complete!")
    print(f"Succeeded: {processed_count}")
    print(f"Failed: {failed_count}")
    print(f"Saved to: {output_dir}")

def test_single_image():
    """Test with a single image."""
    # Test with the first image
    test_files = glob.glob("img/T01_*.tif")
    if test_files:
        test_file = test_files[0]
        filename = os.path.basename(test_file)
        output_path = f"img/circle/test_{filename}"
        
        print(f"Test image: {test_file}")
        if crop_circle_from_image(test_file, output_path):
            print(f"Test successful: {output_path}")
            
            # Print info for original and cropped images
            original = cv2.imread(test_file, cv2.IMREAD_UNCHANGED)
            cropped = cv2.imread(output_path, cv2.IMREAD_UNCHANGED)
            
            print(f"Original size: {original.shape}")
            print(f"Cropped size: {cropped.shape}")
        else:
            print("Test failed")

if __name__ == "__main__":
    print("NEST Image Circular Cropping Tool")
    print("=" * 40)
    
    # First, run a test
    print("1. Testing with a single image...")
    test_single_image()
    
    # User confirmation
    print("\n2. Do you want to process all images? (y/n): ", end="")
    response = input().lower()
    
    if response == 'y' or response == 'yes':
        print("\nStarting to process all images...")
        process_all_images()
    else:
        print("Processing cancelled.") 