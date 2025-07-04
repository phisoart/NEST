import cv2
import numpy as np
import pandas as pd
import glob
import os
import re
from pathlib import Path

def calculate_robust_mean(image_path):
    """
    Calculate the mean value after excluding the cropped outer area (black pixels) 
    and the top/bottom 25% of intensities.
    """
    # Load image
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Could not load image: {image_path}")
        return None
    
    # Convert to grayscale (if necessary)
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Exclude the cropped outer area (black pixels, value=0)
    non_zero_pixels = img[img > 0]
    
    if len(non_zero_pixels) == 0:
        print(f"No valid pixels found: {image_path}")
        return None
    
    # Calculate robust mean after removing top/bottom 25%
    p25 = np.percentile(non_zero_pixels, 25)
    p75 = np.percentile(non_zero_pixels, 75)
    
    # Select only pixels within the 25th-75th percentile range
    filtered_pixels = non_zero_pixels[(non_zero_pixels >= p25) & (non_zero_pixels <= p75)]
    
    if len(filtered_pixels) == 0:
        print(f"No pixels left after filtering: {image_path}")
        return np.mean(non_zero_pixels)  # fallback to all non-zero pixels
    
    robust_mean = np.mean(filtered_pixels)
    return robust_mean

def parse_filename(filename):
    """
    Extract information from filename.
    Example: T23_SA_1_3.tif -> {'time_point': 23, 'sample_type': 'SA', 'cfu': 1, 'replicate': 3}
    Example: T01_Ctr_1.tif -> {'time_point': 1, 'sample_type': 'Ctr', 'cfu': 0, 'replicate': 1}
    """
    # Remove extension from filename
    base_name = filename.replace('.tif', '')
    
    # SA pattern: T##_SA_##_#
    sa_pattern = r'T(\d+)_SA_(\d+)_(\d+)'
    sa_match = re.match(sa_pattern, base_name)
    
    if sa_match:
        time_point = int(sa_match.group(1))
        cfu = int(sa_match.group(2))
        replicate = int(sa_match.group(3))
        return {
            'time_point': time_point,
            'sample_type': 'SA',
            'cfu': cfu,
            'replicate': replicate
        }
    
    # Ctr pattern: T##_Ctr_#
    ctr_pattern = r'T(\d+)_Ctr_(\d+)'
    ctr_match = re.match(ctr_pattern, base_name)
    
    if ctr_match:
        time_point = int(ctr_match.group(1))
        replicate = int(ctr_match.group(2))
        return {
            'time_point': time_point,
            'sample_type': 'Ctr',
            'cfu': 0,
            'replicate': replicate
        }
    
    print(f"Could not recognize filename pattern: {filename}")
    return None

def time_point_to_string(time_point):
    """
    Convert time point to h:mm string format.
    T1 -> 0:00, T2 -> 0:30, T3 -> 1:00, T4 -> 1:30, ...
    """
    minutes = (time_point - 1) * 30
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02d}"

def process_circle_images():
    """Process all images in the 'circle' folder and save to CSV."""
    # Image file path
    circle_dir = "img/circle"
    image_files = glob.glob(os.path.join(circle_dir, "*.tif"))
    
    if not image_files:
        print("No images to process.")
        return
    
    print(f"Analyzing {len(image_files)} images in total...")
    
    # List to store results
    results = []
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        
        # Parse filename
        file_info = parse_filename(filename)
        if file_info is None:
            continue
        
        # Calculate robust mean
        mean_value = calculate_robust_mean(image_path)
        if mean_value is None:
            continue
        
        # Convert time point to string
        time_str = time_point_to_string(file_info['time_point'])
        
        # Save result
        results.append({
            'filename': filename,
            'time_str': time_str,
            'sample_type': file_info['sample_type'],
            'cfu': file_info['cfu'],
            'replicate': file_info['replicate'],
            'mean_intensity': round(mean_value, 2)
        })
        
        # Print progress
        if i % 50 == 0:
            print(f"Progress: {i}/{len(image_files)} ({i/len(image_files)*100:.1f}%)")
    
    # Create and sort DataFrame
    df = pd.DataFrame(results)
    
    # Sort by time, sample_type, cfu, and replicate
    df_sorted = df.sort_values(['time_str', 'sample_type', 'cfu', 'replicate']).reset_index(drop=True)
    
    # Save to CSV file
    output_file = "fluorescence_analysis.csv"
    df_sorted.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\nAnalysis complete!")
    print(f"Processed images: {len(results)}")
    print(f"Saved to: {output_file}")
    print(f"CSV file size: {len(df_sorted)} rows")
    
    # Print sample results
    print("\n=== Sample Results (first 10 rows) ===")
    print(df_sorted.head(10).to_string(index=False))
    
    # Summary statistics
    print(f"\n=== Summary Statistics ===")
    print(f"Count by Sample Type:")
    print(df_sorted['sample_type'].value_counts())
    print(f"\nCFU Count (SA only):")
    sa_data = df_sorted[df_sorted['sample_type'] == 'SA']
    if len(sa_data) > 0:
        print(sa_data['cfu'].value_counts().sort_index())
    
    return df_sorted

def test_single_image():
    """Test with a single image."""
    test_files = glob.glob("img/circle/T01_*.tif")
    if test_files:
        test_file = test_files[0]
        filename = os.path.basename(test_file)
        
        print(f"Test image: {filename}")
        
        # Test filename parsing
        file_info = parse_filename(filename)
        print(f"Parsing result: {file_info}")
        
        # Test robust mean calculation
        mean_value = calculate_robust_mean(test_file)
        print(f"Robust mean: {mean_value}")
        
        # Test time conversion
        if file_info:
            time_str = time_point_to_string(file_info['time_point'])
            print(f"Time string: {time_str}")

if __name__ == "__main__":
    print("NEST Fluorescence Intensity Analysis Tool")
    print("=" * 50)
    
    # First, run a test
    print("1. Testing with a single image...")
    test_single_image()
    
    # User confirmation
    print("\n2. Do you want to analyze all images? (y/n): ", end="")
    response = input().lower()
    
    if response == 'y' or response == 'yes':
        print("\nStarting analysis of all images...")
        process_circle_images()
    else:
        print("Analysis cancelled.") 