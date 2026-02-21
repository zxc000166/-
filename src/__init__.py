"""
2Dto3D Converter - A low-cost, CPU-based tool for converting 2D images to 3D point clouds.

This package provides functionality for:
- Monocular depth estimation using MiDaS models
- Point cloud generation from depth maps
- Structure from Motion (SfM) reconstruction
- Command-line interface for batch processing
"""

from .depth_estimation import DepthEstimator
from .point_cloud_generation import PointCloudGenerator
from .sfm import SfMReconstructor

__version__ = "0.2.0"
__all__ = ["DepthEstimator", "PointCloudGenerator", "SfMReconstructor"]