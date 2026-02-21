
// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const fileList = document.getElementById('file-list');
const actionArea = document.getElementById('action-area');
const uploadBtn = document.getElementById('upload-btn');
const uploadSection = document.getElementById('upload-section');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const statusText = document.getElementById('status-text');
const statusDetail = document.getElementById('status-detail');
const downloadLink = document.getElementById('download-link');
const resetBtn = document.getElementById('reset-btn');

// Constants
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB (increased for PLY)
const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'ply'];

// State
let selectedFiles = [];

// Event Listeners
browseBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
    fileInput.value = ''; // Reset input so same file can be selected again if needed
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    handleFiles(e.dataTransfer.files);
});

uploadBtn.addEventListener('click', uploadFiles);

resetBtn.addEventListener('click', resetInterface);

// Functions
function handleFiles(files) {
    const newFiles = Array.from(files);
    let validCount = 0;

    newFiles.forEach(file => {
        // Validate Extension
        const extension = file.name.split('.').pop().toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            alert(`文件 ${file.name} 格式不支持。仅支持 JPG/PNG/PLY。`);
            return;
        }

        // Validate Size
        if (file.size > MAX_FILE_SIZE) {
            alert(`文件 ${file.name} 过大 (${formatSize(file.size)})。最大允许 50MB。`);
            return;
        }
        
        // Duplicate Check (Simple name check)
        if (selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            return;
        }

        selectedFiles.push(file);
        validCount++;
    });

    if (validCount > 0) {
        updateFileList();
    }
}

function updateFileList() {
    fileList.innerHTML = '';
    
    if (selectedFiles.length > 0) {
        fileList.classList.remove('hidden');
        actionArea.classList.remove('hidden');
    } else {
        fileList.classList.add('hidden');
        actionArea.classList.add('hidden');
    }

    let hasPly = false;

    selectedFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        
        const extension = file.name.split('.').pop().toLowerCase();
        if (extension === 'ply') hasPly = true;

        // Create thumbnail or icon
        if (['jpg', 'jpeg', 'png'].includes(extension)) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'file-thumb';
                item.insertBefore(img, item.firstChild);
            };
            reader.readAsDataURL(file);
        } else {
            // Icon for PLY
            const icon = document.createElement('div');
            icon.className = 'file-thumb';
            icon.style.display = 'flex';
            icon.style.alignItems = 'center';
            icon.style.justifyContent = 'center';
            icon.style.backgroundColor = '#333';
            icon.style.color = 'var(--neon-cyan)';
            icon.innerText = '3D';
            item.insertBefore(icon, item.firstChild);
        }

        item.innerHTML += `
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${formatSize(file.size)}</span>
            </div>
            <span class="remove-file" onclick="removeFile(${index})">&times;</span>
        `;
        fileList.appendChild(item);
    });
    
    // Update button text or warning
    if (hasPly) {
        uploadBtn.innerText = "直接预览 3D 模型";
        uploadBtn.classList.remove('warning-btn');
        uploadBtn.classList.add('success-btn');
    } else if (selectedFiles.length < 2) {
        uploadBtn.innerText = "启动单目深度估计 (建议上传2张以上进行SfM)";
        uploadBtn.classList.remove('success-btn');
        uploadBtn.classList.add('warning-btn');
    } else {
        uploadBtn.innerText = `启动转换 (${selectedFiles.length} 张图片)`;
        uploadBtn.classList.remove('warning-btn');
        uploadBtn.classList.add('success-btn');
    }
}

// Expose to global scope for onclick attribute
window.removeFile = function(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
};

function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function uploadFiles() {
    if (selectedFiles.length === 0) return;

    // UI Updates
    uploadSection.classList.add('hidden');
    progressSection.classList.remove('hidden');
    statusText.innerText = '正在上传...';
    
    // Create progress bar if not exists
    let progressBar = document.getElementById('upload-progress');
    if (!progressBar) {
        progressBar = document.createElement('div');
        progressBar.id = 'upload-progress';
        progressBar.style.width = '0%';
        progressBar.style.height = '4px';
        progressBar.style.backgroundColor = 'var(--neon-cyan)';
        progressBar.style.marginTop = '10px';
        progressBar.style.transition = 'width 0.3s ease';
        const card = document.querySelector('.status-card');
        if(card) card.appendChild(progressBar);
    }
    progressBar.style.width = '0%';
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload', true);

    // Upload Progress
    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            progressBar.style.width = percentComplete + '%';
            statusDetail.innerText = `上传进度: ${Math.round(percentComplete)}%`;
        }
    };

    xhr.onload = function() {
        if (xhr.status === 202) {
            const data = JSON.parse(xhr.responseText);
            if (data.warnings) {
                alert('部分文件上传存在问题:\n' + data.warnings.join('\n'));
            }
            pollStatus(data.task_id);
        } else {
            let errorMsg = '上传失败';
            try {
                const data = JSON.parse(xhr.responseText);
                errorMsg = data.error || errorMsg;
                if (data.details) {
                    errorMsg += '\nDetails: ' + data.details.join('\n');
                }
            } catch (e) {}
            alert(errorMsg);
            resetInterface();
        }
    };

    xhr.onerror = function() {
        alert('网络错误，上传失败。');
        resetInterface();
    };

    xhr.send(formData);
}

async function pollStatus(taskId) {
    statusText.innerText = '处理中...';
    statusDetail.innerText = '正在生成/加载 3D 模型...';
    // Remove progress bar
    const progressBar = document.getElementById('upload-progress');
    if (progressBar) progressBar.style.width = '100%';

    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${taskId}`);
            const data = await response.json();

            if (data.status === 'completed') {
                clearInterval(interval);
                showResult(data);
            } else if (data.status === 'failed') {
                clearInterval(interval);
                alert(`处理失败：${data.error}`);
                resetInterface();
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 1000);
}

function showResult(data) {
    progressSection.classList.add('hidden');
    resultSection.classList.remove('hidden');
    
    // Setup download link
    downloadLink.href = `/api/download/${data.result}`;
    
    // Trigger 3D viewer load (dispatched via custom event or direct call)
    const event = new CustomEvent('loadModel', { 
        detail: { url: `/api/download/${data.result}` } 
    });
    window.dispatchEvent(event);
    
    let info = `转换方法：${data.method}`;
    if (data.method === 'upload') {
        info = '直接预览';
    }
    document.getElementById('model-info').innerText = info;
}

function resetInterface() {
    selectedFiles = [];
    updateFileList();
    resultSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    uploadSection.classList.remove('hidden');
    fileInput.value = '';
    const progressBar = document.getElementById('upload-progress');
    if (progressBar) progressBar.remove();
}
