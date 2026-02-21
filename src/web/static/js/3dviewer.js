import PlyPreviewSkill from './PlyPreviewSkill.js';

let preview;

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('3d-viewer');
    if (!container) return;

    preview = new PlyPreviewSkill('3d-viewer', {
        backgroundColor: 0x111111,
        pointSize: 0.05
    });

    // Listen for custom event from api.js
    window.addEventListener('loadModel', (e) => {
        const url = e.detail.url;
        console.log(`Loading model from: ${url}`);
        
        // Show loading indicator (if any external UI needs update)
        const statusText = document.getElementById('model-info');
        if (statusText) statusText.innerText = '加载中... 0%';

        preview.loadModel(
            url,
            (percent) => {
                if (statusText) statusText.innerText = `加载中... ${Math.round(percent)}%`;
            },
            (geometry) => {
                console.log('Model loaded successfully');
                if (statusText) {
                    const pointCount = geometry.attributes.position.count;
                    let infoText = `点数：${pointCount}`;
                    
                    if (geometry.index) {
                        const faceCount = geometry.index.count / 3;
                        infoText += ` | 面数：${faceCount}`;
                    }
                    
                    statusText.innerText = infoText;
                }
            },
            (error) => {
                console.error('Error loading model:', error);
                if (statusText) statusText.innerText = '加载失败';
                alert('加载 3D 模型出错，请检查文件格式或网络连接。');
            }
        );
    });
});

// Clean up when leaving page (optional for SPA but good practice)
window.addEventListener('beforeunload', () => {
    if (preview) preview.dispose();
});
