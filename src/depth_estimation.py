import cv2
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as transforms

class DepthEstimator:
    def __init__(self, model_type="MiDaS_small"):
        """
        Initialize the depth estimator with MiDaS model.
        Args:
            model_type (str): Type of MiDaS model to use. Options: "MiDaS_small", "DPT_Large", "DPT_Hybrid".
                              "MiDaS_small" is recommended for CPU inference.
        """
        self.device = torch.device("cpu")
        print(f"Loading {model_type} model...")
        
        try:
            # Load MiDaS model from torch hub
            self.model = torch.hub.load("intel-isl/MiDaS", model_type, trust_repo=True)
            self.model.to(self.device)
            self.model.eval()
            
            # Load transforms
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
            if model_type == "DPT_Large" or model_type == "DPT_Hybrid":
                self.transform = midas_transforms.dpt_transform
            else:
                self.transform = midas_transforms.small_transform
        except Exception as e:
            print(f"Warning: Failed to load MiDaS model: {e}")
            print("Running in DUMMY mode (generating fake depth map).")
            self.model = None

    def estimate_depth(self, image_path):
        """
        Estimate depth map from a single RGB image.
        Args:
            image_path (str): Path to the input image.
        Returns:
            numpy.ndarray: Depth map normalized to [0, 1].
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image at {image_path}")
            
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if self.model is None:
                # Return a dummy depth map (gradient)
                h, w = img.shape[:2]
                x = np.linspace(0, 1, w)
                y = np.linspace(0, 1, h)
                xv, yv = np.meshgrid(x, y)
                return (xv + yv) / 2.0

            # Transform input
            input_batch = self.transform(img).to(self.device)
            
            # Predict
            with torch.no_grad():
                prediction = self.model(input_batch)
                
                # Resize to original resolution
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            
            depth_map = prediction.cpu().numpy()
            
            # Normalize depth map to 0-1 range for visualization/processing
            depth_min = depth_map.min()
            depth_max = depth_map.max()
            depth_map_normalized = (depth_map - depth_min) / (depth_max - depth_min)
            
            return depth_map_normalized
            
        except Exception as e:
            print(f"Error estimating depth: {e}")
            return None
