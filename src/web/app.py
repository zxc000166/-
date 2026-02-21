
import os
import uuid
import time
import shutil
import logging
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS
from PIL import Image

# Import our core logic
import sys
# Add project root to path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.depth_estimation import DepthEstimator
from src.point_cloud_generation import PointCloudGenerator
from src.sfm import SfMReconstructor

# Configuration
UPLOAD_FOLDER = os.path.abspath('uploads')
RESULTS_FOLDER = os.path.abspath('results')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'ply'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Increased to 50MB for PLY files
MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB per file strict check

# Initialize Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
CORS(app)

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Task Queue (Simple in-memory for demo)
executor = ThreadPoolExecutor(max_workers=2) # Increased workers
tasks = {}

def validate_image(stream):
    """
    Strictly validate image using PIL.
    Returns (is_valid, error_message)
    """
    try:
        img = Image.open(stream)
        img.verify() # Verify file integrity
        
        # Reset stream position after verify
        stream.seek(0)
        
        # Check format
        if img.format.lower() not in ['jpeg', 'png', 'jpg']:
             return False, f"Invalid image format: {img.format}"
             
        return True, None
    except Exception as e:
        return False, f"Corrupted or invalid image file: {str(e)}"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def scan_file(filepath):
    """
    Simulated virus scan.
    In production, integrate with ClamAV or similar.
    """
    # Simulate scan time
    # time.sleep(0.1) 
    return True

def process_task(task_id, file_paths):
    """Background task to process images to 3D."""
    tasks[task_id]['status'] = 'processing'
    output_filename = f"{task_id}.ply"
    output_path = os.path.join(RESULTS_FOLDER, output_filename)
    
    try:
        start_time = time.time()
        
        # 0. Check if Direct PLY Upload
        if len(file_paths) == 1 and file_paths[0].lower().endswith('.ply'):
             shutil.copy(file_paths[0], output_path)
             tasks[task_id]['status'] = 'completed'
             tasks[task_id]['result'] = output_filename
             tasks[task_id]['method'] = 'upload'
             logger.info(f"Task {task_id}: PLY Upload success")
             return

        # 1. Decision: SfM or Monocular
        if len(file_paths) >= 2:
            logger.info(f"Task {task_id}: Attempting SfM with {len(file_paths)} images")
            reconstructor = SfMReconstructor(feature_type="SIFT")
            result = reconstructor.reconstruct_from_images(file_paths)
            
            if result["success"]:
                reconstructor.create_point_cloud(result, output_path)
                tasks[task_id]['status'] = 'completed'
                tasks[task_id]['result'] = output_filename
                tasks[task_id]['method'] = 'sfm'
                logger.info(f"Task {task_id}: SfM success")
                return
            else:
                logger.warning(f"Task {task_id}: SfM failed ({result.get('error')}), falling back to monocular")
        
        # 2. Fallback / Monocular
        logger.info(f"Task {task_id}: Running Monocular Depth Estimation on first image")
        # Use the first image
        input_image = file_paths[0]
        
        estimator = DepthEstimator(model_type='MiDaS_small')
        depth_map = estimator.estimate_depth(input_image)
        
        if depth_map is None:
             raise Exception("深度估计失败")
             
        generator = PointCloudGenerator()
        pcd = generator.depth_to_pointcloud(depth_map, input_image, output_path)
        
        if pcd:
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['result'] = output_filename
            tasks[task_id]['method'] = 'monocular'
            logger.info(f"Task {task_id}: Monocular success")
        else:
            raise Exception("点云生成失败")
            
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
    finally:
        # Cleanup uploaded files? keeping them for debug for now
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': '未找到文件部分'}), 400
    
    files = request.files.getlist('files')
    if not files or len(files) == 0 or files[0].filename == '':
        return jsonify({'error': '未选择文件'}), 400
        
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(app.config['UPLOAD_FOLDER'], task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    saved_paths = []
    errors = []
    
    for file in files:
        if not file:
            continue
            
        filename = secure_filename(file.filename)
        
        # 1. Check Extension
        if not allowed_file(filename):
            errors.append(f"{filename}: 不支持的文件类型")
            continue
            
        # 2. Check Magic Numbers / Content
        if filename.lower().endswith('.ply'):
             # Basic PLY validation (read first few bytes)
             try:
                 header = file.read(3)
                 file.seek(0)
                 if header != b'ply':
                     errors.append(f"{filename}: 无效的 PLY 文件头")
                     continue
             except:
                 errors.append(f"{filename}: 无法读取文件")
                 continue
        else:
            is_valid, error_msg = validate_image(file.stream)
            if not is_valid:
                errors.append(f"{filename}: {error_msg}")
                continue
            
        # 3. Save
        filepath = os.path.join(task_dir, filename)
        try:
            file.save(filepath)
            
            # 4. Check Size (Double check actual saved size)
            if os.path.getsize(filepath) > MAX_FILE_SIZE:
                os.remove(filepath)
                errors.append(f"{filename}: 文件过大 (最大 10MB)")
                continue
                
            # 5. Virus Scan
            if not scan_file(filepath):
                 os.remove(filepath)
                 errors.append(f"{filename}: 安全检查未通过")
                 continue
                 
            saved_paths.append(filepath)
            
        except Exception as e:
            errors.append(f"{filename}: 保存失败 - {str(e)}")

    if not saved_paths:
        # Cleanup
        shutil.rmtree(task_dir, ignore_errors=True)
        return jsonify({'error': '所有文件均上传失败', 'details': errors}), 400
        
    # Create task
    tasks[task_id] = {
        'id': task_id,
        'status': 'queued',
        'submitted_at': time.time(),
        'files': len(saved_paths),
        'warnings': errors if errors else None
    }
    
    # Submit to background executor
    executor.submit(process_task, task_id, saved_paths)
    
    response_data = {
        'message': '上传成功，开始处理', 
        'task_id': task_id,
        'files_count': len(saved_paths)
    }
    
    if errors:
        response_data['warnings'] = errors
        
    return jsonify(response_data), 202

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': '任务未找到'}), 404
    return jsonify(task)

@app.route('/api/download/<filename>', methods=['GET'])
def download_result(filename):
    return send_from_directory(app.config['RESULTS_FOLDER'], filename, as_attachment=True)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': '文件过大（最大 16MB）'}), 413

if __name__ == '__main__':
    # Use FLASK_DEBUG environment variable, default to True for dev
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
