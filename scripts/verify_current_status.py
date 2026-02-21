#!/usr/bin/env python3
"""
Current Status Verification Script for 2Dto3D Converter

This script verifies that all current functionality is working correctly
and generates a status report for Phase 1 completion.
"""

import os
import sys
import time
import cv2
import numpy as np
from pathlib import Path

def test_module_imports():
    """Test that all modules can be imported successfully."""
    print("Testing module imports...")
    try:
        from src.depth_estimation import DepthEstimator
        from src.point_cloud_generation import PointCloudGenerator
        from src.sfm import SfMReconstructor
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_depth_estimation():
    """Test depth estimation functionality."""
    print("\nTesting depth estimation...")
    try:
        from src.depth_estimation import DepthEstimator
        
        # Create a test image
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite("temp_test.jpg", test_img)
        
        # Test depth estimation
        estimator = DepthEstimator(model_type="MiDaS_small")
        start_time = time.time()
        depth_map = estimator.estimate_depth("temp_test.jpg")
        elapsed_time = time.time() - start_time
        
        if depth_map is not None:
            print(f"✅ Depth estimation successful in {elapsed_time:.2f}s")
            print(f"   - Output shape: {depth_map.shape}")
            print(f"   - Value range: [{depth_map.min():.3f}, {depth_map.max():.3f}]")
            success = True
        else:
            print("❌ Depth estimation failed")
            success = False
            
        # Cleanup
        if os.path.exists("temp_test.jpg"):
            os.remove("temp_test.jpg")
            
        return success
        
    except Exception as e:
        print(f"❌ Depth estimation error: {e}")
        return False

def test_point_cloud_generation():
    """Test point cloud generation functionality."""
    print("\nTesting point cloud generation...")
    try:
        from src.depth_estimation import DepthEstimator
        from src.point_cloud_generation import PointCloudGenerator
        
        # Create test data
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite("temp_test.jpg", test_img)
        
        # Generate depth map
        estimator = DepthEstimator(model_type="MiDaS_small")
        depth_map = estimator.estimate_depth("temp_test.jpg")
        
        if depth_map is None:
            print("❌ Cannot test point cloud - depth estimation failed")
            return False
            
        # Generate point cloud
        generator = PointCloudGenerator()
        start_time = time.time()
        pcd = generator.depth_to_pointcloud(depth_map, "temp_test.jpg", "temp_output.ply")
        elapsed_time = time.time() - start_time
        
        if pcd is not None:
            print(f"✅ Point cloud generation successful in {elapsed_time:.2f}s")
            print(f"   - Vertices: {len(pcd.vertices)}")
            print(f"   - Colors: {len(pcd.colors)}")
            
            # Check output file
            if os.path.exists("temp_output.ply"):
                file_size = os.path.getsize("temp_output.ply")
                print(f"   - Output file size: {file_size} bytes")
                success = True
            else:
                print("❌ Output file not created")
                success = False
        else:
            print("❌ Point cloud generation failed")
            success = False
            
        # Cleanup
        for file in ["temp_test.jpg", "temp_output.ply"]:
            if os.path.exists(file):
                os.remove(file)
                
        return success
        
    except Exception as e:
        print(f"❌ Point cloud generation error: {e}")
        return False

def test_sfm_placeholder():
    """Test SfM module (placeholder implementation)."""
    print("\nTesting SfM module...")
    try:
        from src.sfm import SfMReconstructor
        
        # Test initialization
        sfm = SfMReconstructor(feature_type="SIFT")
        print("✅ SfM module initialized successfully")
        
        # Test with insufficient images (should fail gracefully)
        result = sfm.reconstruct_from_images(["nonexistent.jpg"])
        if not result["success"] and "at least 2 images" in result.get("error", ""):
            print("✅ SfM validation working correctly")
            return True
        else:
            print("❌ SfM validation not working as expected")
            return False
            
    except Exception as e:
        print(f"❌ SfM module error: {e}")
        return False

def test_cli_functionality():
    """Test CLI functionality."""
    print("\nTesting CLI functionality...")
    try:
        import subprocess
        import sys
        
        # Create test image
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        cv2.imwrite("cli_test.jpg", test_img)
        
        # Test CLI help
        result = subprocess.run([sys.executable, "cli.py", "--help"], 
                               capture_output=True, text=True)
        if result.returncode == 0 and "Convert a 2D image to a 3D point cloud" in result.stdout:
            print("✅ CLI help working")
        else:
            print("❌ CLI help not working")
            return False
            
        # Test actual conversion (this might take time)
        print("Testing CLI conversion (this may take a moment)...")
        result = subprocess.run([sys.executable, "cli.py", "-i", "cli_test.jpg", "-o", "cli_output.ply"], 
                               capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists("cli_output.ply"):
            file_size = os.path.getsize("cli_output.ply")
            print(f"✅ CLI conversion successful (output: {file_size} bytes)")
            success = True
        else:
            print(f"❌ CLI conversion failed (return code: {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}...")
            success = False
            
        # Cleanup
        for file in ["cli_test.jpg", "cli_output.ply"]:
            if os.path.exists(file):
                os.remove(file)
                
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ CLI test timed out")
        return False
    except Exception as e:
        print(f"❌ CLI test error: {e}")
        return False

def generate_status_report():
    """Generate a comprehensive status report."""
    print("\n" + "="*60)
    print("PHASE 1 STATUS VERIFICATION REPORT")
    print("="*60)
    print(f"Verification Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version}")
    print("-" * 60)
    
    results = {}
    
    # Run all tests
    results['Module Imports'] = test_module_imports()
    results['Depth Estimation'] = test_depth_estimation()
    results['Point Cloud Generation'] = test_point_cloud_generation()
    results['SfM Module'] = test_sfm_placeholder()
    results['CLI Functionality'] = test_cli_functionality()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print("-" * 60)
    print(f"Overall Status: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Phase 1 is ready for Phase 2!")
        print("\nNext steps:")
        print("1. Review PLAN_PHASE_2.md for detailed Day 3-4 plan")
        print("2. Run 'run_tests.bat' for automated testing")
        print("3. Begin SfM implementation as outlined in the plan")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed - please fix before proceeding to Phase 2")
        return False

if __name__ == "__main__":
    success = generate_status_report()
    sys.exit(0 if success else 1)