import numpy as np
import trimesh
import cv2

class PointCloudGenerator:
    def __init__(self):
        pass

    def depth_to_pointcloud(self, depth_map, rgb_image_path, output_path="output.ply"):
        """
        Convert depth map and RGB image to a colored point cloud.
        Args:
            depth_map (numpy.ndarray): Normalized depth map (H, W).
            rgb_image_path (str): Path to the RGB image.
            output_path (str): Path to save the point cloud (.ply or .obj).
        Returns:
            trimesh.PointCloud: The generated point cloud object.
        """
        try:
            # Read RGB image
            rgb_img = cv2.imread(rgb_image_path)
            if rgb_img is None:
                raise ValueError(f"Could not read image at {rgb_image_path}")
            
            rgb_img = cv2.cvtColor(rgb_img, cv2.COLOR_BGR2RGB)
            
            # Ensure depth map and RGB image have the same resolution
            if depth_map.shape[:2] != rgb_img.shape[:2]:
                 depth_map = cv2.resize(depth_map, (rgb_img.shape[1], rgb_img.shape[0]))

            height, width = depth_map.shape
            
            # Camera intrinsics (approximated)
            # Assuming a standard field of view (approx 60 degrees)
            # fx = fy = width / (2 * tan(fov/2))
            fov = 60
            fx = width / (2 * np.tan(np.radians(fov / 2)))
            fy = fx
            cx = width / 2
            cy = height / 2
            
            # Generate mesh grid
            x, y = np.meshgrid(np.arange(width), np.arange(height))
            
            # Back-project to 3D
            # Z = depth (we need to invert or scale it appropriately)
            # MiDaS outputs inverse depth (disparity), so Z ~ 1 / depth
            # However, for normalized 0-1 depth map from estimate_depth, we can treat it as relative depth directly or inverse.
            # Usually MiDaS output is relative inverse depth.
            # Let's assume the normalized output is proportional to disparity.
            # So Z = 1 / (depth_map + epsilon)
            
            # Simple linear mapping for visualization if we treat it as distance (which is not strictly true for MiDaS but often used for simple effects)
            # Or use 1/d. Let's try 1/d with a scale.
            
            epsilon = 1e-6
            z = 1.0 / (depth_map + epsilon)
            
            # Clip Z to avoid flying pixels at infinity
            z = np.clip(z, 0, 100) # Arbitrary scale
            
            # X = (u - cx) * Z / fx
            # Y = (v - cy) * Z / fy
            
            x_3d = (x - cx) * z / fx
            y_3d = (y - cy) * z / fy
            
            # Stack to (N, 3)
            vertices = np.stack((x_3d.flatten(), y_3d.flatten(), z.flatten()), axis=1)
            colors = rgb_img.reshape(-1, 3)
            
            # Create PointCloud using trimesh
            pcd = trimesh.points.PointCloud(vertices=vertices, colors=colors)
            
            # Save
            pcd.export(output_path)
            print(f"Point cloud saved to {output_path}")
            
            return pcd
            
        except Exception as e:
            print(f"Error generating point cloud: {e}")
            return None
