import cv2
import numpy as np
from typing import List, Dict, Tuple
import trimesh

class SfMReconstructor:
    """
    Structure from Motion reconstructor for multi-view 3D reconstruction.
    
    This class implements the complete SfM pipeline:
    1. Feature extraction and matching
    2. Camera pose estimation
    3. Triangulation
    4. Bundle adjustment (optional)
    5. Dense point cloud generation
    """
    
    def __init__(self, feature_type: str = "SIFT", matcher_type: str = "FLANN"):
        """
        Initialize the SfM reconstructor.
        
        Args:
            feature_type: Type of feature detector ('SIFT', 'ORB', 'AKAZE')
            matcher_type: Type of feature matcher ('FLANN', 'BF')
        """
        self.feature_type = feature_type
        self.matcher_type = matcher_type
        self.detector = None
        self.matcher = None
        self._initialize_detectors()
        
    def _initialize_detectors(self):
        """Initialize feature detectors and matchers."""
        # Initialize feature detector
        if self.feature_type == "SIFT":
            self.detector = cv2.SIFT_create()
        elif self.feature_type == "ORB":
            self.detector = cv2.ORB_create(nfeatures=5000)
        elif self.feature_type == "AKAZE":
            self.detector = cv2.AKAZE_create()
        else:
            raise ValueError(f"Unsupported feature type: {self.feature_type}")
            
        # Initialize matcher
        if self.matcher_type == "FLANN":
            if self.feature_type == "ORB":
                # ORB uses Hamming distance
                FLANN_INDEX_LSH = 6
                index_params = dict(algorithm=FLANN_INDEX_LSH,
                                   table_number=6,
                                   key_size=12,
                                   multi_probe_level=1)
            else:
                # SIFT uses L2 distance
                FLANN_INDEX_KDTREE = 1
                index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
                
            search_params = dict(checks=50)
            self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
        else:
            # Brute force matcher
            if self.feature_type == "ORB":
                self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            else:
                self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
    
    def extract_features(self, image_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract features from a single image.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Tuple of (keypoints, descriptors)
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
            
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        
        if descriptors is None:
            descriptors = np.array([])
            keypoints = []
            
        return keypoints, descriptors
    
    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> List[cv2.DMatch]:
        """
        Match features between two sets of descriptors.
        
        Args:
            desc1: First set of descriptors
            desc2: Second set of descriptors
            
        Returns:
            List of good matches
        """
        if desc1 is None or desc2 is None or len(desc1) == 0 or len(desc2) == 0:
            return []
            
        try:
            if self.matcher_type == "FLANN" or self.feature_type == "SIFT":
                # For k-NN matching with SIFT/FLANN
                matches = self.matcher.knnMatch(desc1, desc2, k=2)
                
                # Apply Lowe's ratio test
                good_matches = []
                for match_pair in matches:
                    if len(match_pair) == 2:
                        m, n = match_pair
                        if m.distance < 0.7 * n.distance:
                            good_matches.append(m)
                return good_matches
            else:
                # For BF matching (e.g. ORB with crossCheck=True)
                matches = self.matcher.match(desc1, desc2)
                matches = sorted(matches, key=lambda x: x.distance)
                return matches[:min(len(matches), 500)] # Return top 500
                
        except Exception as e:
            print(f"Matching failed: {e}")
            return []
    
    def estimate_poses(self, kp1: List[cv2.KeyPoint], kp2: List[cv2.KeyPoint], 
                      matches: List[cv2.DMatch]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Estimate camera poses from matched features.
        
        Args:
            kp1: Keypoints from first image
            kp2: Keypoints from second image
            matches: Matched features
            
        Returns:
            Tuple of (rotation_matrix, translation_vector)
        """
        if len(matches) < 8:
            raise ValueError(f"Not enough matches for pose estimation: {len(matches)} < 8")

        # Extract matched points
        pts1 = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        pts2 = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # Find essential matrix
        # Assuming intrinsic matrix K is identity or estimated (here using placeholder K)
        K = self._get_camera_matrix()  
        
        # Calculate Essential Matrix
        E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
        
        if E is None or E.shape != (3, 3):
             # Fallback or retry logic could go here
            raise ValueError("Could not estimate essential matrix")
        
        # Recover pose
        # We pass points to recoverPose to disambiguate the 4 possible solutions
        points, R, t, mask = cv2.recoverPose(E, pts1, pts2, K)
        
        return R, t
    
    def triangulate_points(self, kp1: List[cv2.KeyPoint], kp2: List[cv2.KeyPoint],
                          matches: List[cv2.DMatch], R: np.ndarray, t: np.ndarray) -> np.ndarray:
        """
        Triangulate 3D points from matched features and camera poses.
        
        Args:
            kp1: Keypoints from first image
            kp2: Keypoints from second image
            matches: Matched features
            R: Rotation matrix
            t: Translation vector
            
        Returns:
            Array of 3D points
        """
        K = self._get_camera_matrix()
        
        # Projection matrices
        # P1 is at origin [I|0]
        P1 = np.dot(K, np.hstack((np.eye(3), np.zeros((3, 1)))))
        # P2 is at [R|t]
        P2 = np.dot(K, np.hstack((R, t)))
        
        # Extract matched points
        pts1 = np.float32([kp1[m.queryIdx].pt for m in matches]).T
        pts2 = np.float32([kp2[m.trainIdx].pt for m in matches]).T
        
        # Triangulate
        points_4d = cv2.triangulatePoints(P1, P2, pts1, pts2)
        
        # Convert to 3D (homogeneous to euclidean)
        points_3d = points_4d[:3] / points_4d[3]
        
        return points_3d.T
    
    def reconstruct_from_images(self, image_paths: List[str]) -> Dict:
        """
        Perform complete SfM reconstruction from multiple images.
        
        Args:
            image_paths: List of paths to input images
            
        Returns:
            Dictionary containing reconstruction results
        """
        # TODO: Implement complete SfM pipeline
        # This is a placeholder implementation
        
        if len(image_paths) < 2:
            return {"success": False, "error": "Need at least 2 images for SfM"}
        
        try:
            # Extract features from all images
            features = []
            for path in image_paths:
                kp, desc = self.extract_features(path)
                features.append((kp, desc))
            
            # For now, just process the first image pair
            kp1, desc1 = features[0]
            kp2, desc2 = features[1]
            
            # Match features
            matches = self.match_features(desc1, desc2)
            
            if len(matches) < 50:
                return {
                    "success": False, 
                    "error": f"Too few matches: {len(matches)}",
                    "fallback_needed": True
                }
            
            # Estimate poses
            R, t = self.estimate_poses(kp1, kp2, matches)
            
            # Triangulate points
            points_3d = self.triangulate_points(kp1, kp2, matches, R, t)
            
            # Get colors for 3D points
            img1 = cv2.imread(image_paths[0])
            img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
            
            colors = []
            for m in matches:
                pt = kp1[m.queryIdx].pt
                x, y = int(pt[0]), int(pt[1])
                # Ensure coordinates are within bounds
                x = max(0, min(x, img1_rgb.shape[1] - 1))
                y = max(0, min(y, img1_rgb.shape[0] - 1))
                colors.append(img1_rgb[y, x])
            
            colors = np.array(colors)
            
            return {
                "success": True,
                "points_3d": points_3d,
                "colors": colors,
                "num_images": len(image_paths),
                "num_matches": len(matches),
                "cameras": [
                    {"rotation": np.eye(3), "translation": np.zeros(3)},
                    {"rotation": R, "translation": t.flatten()}
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback_needed": True
            }
    
    def _get_camera_matrix(self) -> np.ndarray:
        """Get default camera matrix (approximate)."""
        # Default camera matrix for 640x480 image
        K = np.array([
            [800, 0, 320],
            [0, 800, 240],
            [0, 0, 1]
        ], dtype=np.float32)
        return K
    
    def create_point_cloud(self, reconstruction_result: Dict, output_path: str = None) -> trimesh.PointCloud:
        """
        Create a point cloud from reconstruction results.
        
        Args:
            reconstruction_result: Result from reconstruct_from_images
            output_path: Optional path to save the point cloud
            
        Returns:
            trimesh PointCloud object
        """
        if not reconstruction_result["success"]:
            raise ValueError("Reconstruction failed, cannot create point cloud")
        
        points = reconstruction_result["points_3d"]
        colors = reconstruction_result["colors"]
        
        # Filter out points that are too far or have invalid coordinates
        valid_mask = np.all(np.isfinite(points), axis=1)
        valid_mask &= np.linalg.norm(points, axis=1) < 100  # Remove outliers
        
        points = points[valid_mask]
        colors = colors[valid_mask]
        
        # Create point cloud
        pcd = trimesh.PointCloud(vertices=points, colors=colors)
        
        if output_path:
            pcd.export(output_path)
            
        return pcd