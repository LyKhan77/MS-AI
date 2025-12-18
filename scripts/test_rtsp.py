"""
RTSP Camera Connection Test Script
Tests connection to IP camera and verifies stream quality
"""

import cv2
import argparse
import time
from datetime import datetime

def test_rtsp_connection(rtsp_url, duration=10, save_frame=True):
    """
    Test RTSP camera connection
    
    Args:
        rtsp_url: RTSP stream URL
        duration: Test duration in seconds
        save_frame: Whether to save a test frame
    """
    print("="*60)
    print("RTSP Camera Connection Test")
    print("="*60)
    print(f"\nRTSP URL: {rtsp_url}")
    print(f"Test duration: {duration} seconds\n")
    
    # Try to connect
    print("Connecting to camera...")
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print("✗ Failed to connect to RTSP stream")
        print("  Possible issues:")
        print("  - Check network connection")
        print("  - Verify RTSP URL and credentials")
        print("  - Ensure camera is accessible from Jetson")
        return False
    
    print("✓ Connection established\n")
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Stream Properties:")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps if fps > 0 else 'Unknown'}\n")
    
    # Read frames and measure actual FPS
    print("Reading frames...")
    frame_count = 0
    start_time = time.time()
    last_frame = None
    
    while time.time() - start_time < duration:
        ret, frame = cap.read()
        
        if not ret:
            print("✗ Failed to read frame")
            break
        
        frame_count += 1
        last_frame = frame
        
        # Print progress every second
        elapsed = time.time() - start_time
        if int(elapsed) > int(elapsed - 0.1):  # Roughly every second
            actual_fps = frame_count / elapsed
            print(f"  Elapsed: {int(elapsed)}s | Frames: {frame_count} | FPS: {actual_fps:.2f}")
    
    # Calculate final statistics
    total_time = time.time() - start_time
    actual_fps = frame_count / total_time if total_time > 0 else 0
    
    print(f"\nTest Results:")
    print(f"  Total frames captured: {frame_count}")
    print(f"  Actual FPS: {actual_fps:.2f}")
    print(f"  Test duration: {total_time:.2f}s")
    
    # Save a test frame
    if save_frame and last_frame is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_frame_{timestamp}.jpg"
        cv2.imwrite(filename, last_frame)
        print(f"\n✓ Test frame saved: {filename}")
    
    # Cleanup
    cap.release()
    
    # Verdict
    print("\n" + "="*60)
    if frame_count > 0 and actual_fps > 15:
        print("✓ RTSP connection test PASSED")
        print("  Camera is ready for use")
    elif frame_count > 0:
        print("⚠ RTSP connection test WARNING")
        print(f"  FPS is low ({actual_fps:.2f}). Expected > 15 FPS")
        print("  Check network bandwidth and camera settings")
    else:
        print("✗ RTSP connection test FAILED")
        print("  No frames received from camera")
    
    print("="*60)
    
    return frame_count > 0

def main():
    parser = argparse.ArgumentParser(description='Test RTSP camera connection')
    parser.add_argument(
        '--rtsp-url',
        type=str,
        default='rtsp://admin:gspe-intercon@192.168.0.64:554/Streaming/Channels/1',
        help='RTSP stream URL'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=10,
        help='Test duration in seconds'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save test frame'
    )
    
    args = parser.parse_args()
    
    success = test_rtsp_connection(
        args.rtsp_url,
        duration=args.duration,
        save_frame=not args.no_save
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
