# 2Dto3D Converter

A low-cost, CPU-based tool for independent developers to convert 2D RGB images into 3D point clouds/meshes using MiDaS depth estimation.

## Features
- **Monocular Depth Estimation**: Uses MiDaS (Small/Hybrid/Large) models.
- **Point Cloud Generation**: Converts depth maps to colored PLY point clouds.
- **CPU Optimized**: Designed to run on standard hardware without GPU requirements.
- **CLI Interface**: Simple command-line tool for conversion.

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### CLI
Convert a single image to a point cloud:
```bash
python cli.py -i input.jpg -o output.ply -m MiDaS_small
```

Options:
- `-i, --input`: Path to input image (required).
- `-o, --output`: Path to output file (default: output.ply).
- `-m, --model`: Model type (default: MiDaS_small). Options: `MiDaS_small`, `DPT_Large`, `DPT_Hybrid`.

### Python API
```python
from src.depth_estimation import DepthEstimator
from src.point_cloud_generation import PointCloudGenerator

# Estimate depth
estimator = DepthEstimator(model_type="MiDaS_small")
depth_map = estimator.estimate_depth("input.jpg")

# Generate point cloud
generator = PointCloudGenerator()
generator.depth_to_pointcloud(depth_map, "input.jpg", "output.ply")
```

## Deployment

To deploy using Docker:

1. Build and run the container:
   ```bash
   docker-compose up -d --build
   ```
2. Access the Web Interface at http://localhost:5000

For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Testing
Run unit tests:
```bash
pytest tests/
```

## License
MIT License
