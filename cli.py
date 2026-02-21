import click
import os
import glob
from src.depth_estimation import DepthEstimator
from src.point_cloud_generation import PointCloudGenerator
from src.sfm import SfMReconstructor

@click.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option('--input', '-i', required=False, help='Path to input image or directory')
@click.option('--output', '-o', default='output.ply', help='Path to output PLY/OBJ file')
@click.option('--model', '-m', default='MiDaS_small', help='Model type: MiDaS_small, DPT_Large, DPT_Hybrid')
@click.option('--sfm/--no-sfm', default=True, help='Enable/Disable SfM reconstruction')
@click.pass_context
def main(ctx, input, output, model, sfm):
    """
    Convert a 2D image to a 3D point cloud.
    
    If input is a directory or glob pattern, and --sfm is enabled, 
    it will attempt Structure from Motion reconstruction.
    """
    # Handle wildcard expansion by shell (PowerShell/Bash often expands before python sees it)
    # If shell expands "images/*.jpg" to "images/1.jpg images/2.jpg", 
    # input will be "images/1.jpg" and the rest will be in ctx.args
    
    input_files = []
    
    # 1. Collect all potential input arguments
    potential_inputs = []
    if input:
        potential_inputs.append(input)
    potential_inputs.extend(ctx.args)
    
    # 2. Process inputs (expand globs if they were passed as strings, or use direct paths)
    for path_str in potential_inputs:
        # Check if it looks like a glob pattern
        if '*' in path_str or '?' in path_str:
            expanded = sorted(glob.glob(path_str))
            input_files.extend(expanded)
        else:
            # It's a direct path (or shell already expanded it)
            if os.path.exists(path_str):
                # If directory, expand content
                if os.path.isdir(path_str):
                     input_files.extend(sorted(glob.glob(os.path.join(path_str, "*.[jJ][pP][gG]"))) + \
                                        sorted(glob.glob(os.path.join(path_str, "*.[pP][nN][gG]"))))
                else:
                    input_files.append(path_str)
            else:
                # Might be a glob pattern that didn't match anything yet, or invalid path
                # Try globbing just in case
                expanded = sorted(glob.glob(path_str))
                if expanded:
                    input_files.extend(expanded)
    
    # Remove duplicates and sort
    input_files = sorted(list(set(input_files)))

    if not input_files:
        print("Error: No input files found.")
        
        if not potential_inputs:
             print("Please provide input via -i/--input.")
        else:
            print("\nDiagnostics:")
            for path_str in potential_inputs:
                if '*' in path_str or '?' in path_str:
                    # It's a glob pattern
                    dirname = os.path.dirname(path_str)
                    if dirname and not os.path.exists(dirname):
                        print(f"  [!] Directory not found: '{dirname}'")
                        print(f"      (Pattern was: '{path_str}')")
                    else:
                        print(f"  [!] No files matched the pattern: '{path_str}'")
                        if dirname:
                             print(f"      (Directory '{dirname}' exists)")
                        else:
                             print(f"      (Checked current directory)")
                else:
                    # It's a direct path
                    if not os.path.exists(path_str):
                        print(f"  [!] File or directory not found: '{path_str}'")
        
        print("\nExample usage:")
        print("  python cli.py -i 'images/*.jpg'")
        print("  python cli.py -i images/my_photo.jpg")
        return

    # Try SfM if multiple images and enabled
    if sfm and len(input_files) >= 2:
        print(f"Attempting SfM reconstruction with {len(input_files)} images...")
        try:
            reconstructor = SfMReconstructor(feature_type="SIFT")
            result = reconstructor.reconstruct_from_images(input_files)
            
            if result["success"]:
                print("SfM reconstruction successful!")
                print(f"Generated {len(result['points_3d'])} 3D points.")
                reconstructor.create_point_cloud(result, output)
                print(f"Point cloud saved to {output}")
                return
            else:
                print(f"SfM failed: {result.get('error', 'Unknown error')}")
                print("Falling back to single-image depth estimation...")
        except Exception as e:
            print(f"SfM error: {e}")
            print("Falling back to single-image depth estimation...")

    # Fallback or Single Image Mode
    print(f"Processing {input_files[0]} with {model}...")
    
    # 1. Estimate Depth
    estimator = DepthEstimator(model_type=model)
    depth_map = estimator.estimate_depth(input_files[0])
    
    if depth_map is None:
        print("Depth estimation failed.")
        return

    # 2. Generate Point Cloud
    generator = PointCloudGenerator()
    pcd = generator.depth_to_pointcloud(depth_map, input_files[0], output)
    
    if pcd:
        print("Conversion successful!")
    else:
        print("Point cloud generation failed.")

if __name__ == '__main__':
    main()
