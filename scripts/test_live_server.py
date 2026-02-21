import os
import requests
import time
import uuid

def test_full_flow():
    base_url = "http://127.0.0.1:5000"
    
    # 1. Create a dummy image
    from PIL import Image
    import io
    
    img_byte_arr = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    # 2. Upload
    print(f"Uploading file to {base_url}/api/upload...")
    files = {'files': ('test_flow.jpg', img_byte_arr, 'image/jpeg')}
    try:
        resp = requests.post(f"{base_url}/api/upload", files=files)
        if resp.status_code != 202:
            print(f"Upload failed: {resp.status_code} {resp.text}")
            return
        
        data = resp.json()
        task_id = data['task_id']
        print(f"Upload success. Task ID: {task_id}")
        
        # 3. Poll Status
        print("Polling status...")
        for _ in range(30): # Wait up to 60 seconds
            status_resp = requests.get(f"{base_url}/api/status/{task_id}")
            status_data = status_resp.json()
            status = status_data['status']
            print(f"Status: {status}")
            
            if status == 'completed':
                result_filename = status_data['result']
                print(f"Task completed. Result file: {result_filename}")
                
                # 4. Download
                download_url = f"{base_url}/api/download/{result_filename}"
                print(f"Downloading from {download_url}...")
                dl_resp = requests.get(download_url)
                
                if dl_resp.status_code == 200:
                    print(f"Download success! File size: {len(dl_resp.content)} bytes")
                    
                    # Verify content (PLY header)
                    if dl_resp.content.startswith(b"ply"):
                        print("File content verification passed (starts with 'ply').")
                    else:
                        print("File content verification FAILED (does not start with 'ply').")
                else:
                    print(f"Download FAILED: {dl_resp.status_code}")
                return
                
            elif status == 'failed':
                print(f"Task failed: {status_data.get('error')}")
                return
            
            time.sleep(2)
            
        print("Timed out waiting for task completion.")
        
    except Exception as e:
        print(f"Test exception: {e}")

if __name__ == "__main__":
    test_full_flow()
