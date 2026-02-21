# 3D Online Preview Module Documentation

This module provides a high-performance online 3D preview capability for PLY models, integrated into the 2D-to-3D conversion platform.

## Features

- **Format Support**: Supports ASCII and Binary PLY formats.
- **Rendering**: Uses Three.js for WebGL rendering with OrbitControls.
- **Auto-Scaling**: Automatically centers and scales models to fit the viewport.
- **Progress Tracking**: Real-time loading progress feedback.
- **Error Handling**: Robust error catching and user notification.
- **Large File Support**: Optimized for files >50MB (dependent on client RAM).

## File Structure

- `src/web/static/js/PlyPreviewSkill.js`: Core logic class.
- `src/web/static/js/3dviewer.js`: Integration script that initializes the viewer.
- `src/web/static/js/api.js`: Handles file upload and status polling.
- `src/web/app.py`: Backend support for PLY file upload and serving.

## API Usage (PlyPreviewSkill.js)

The `PlyPreviewSkill` class encapsulates the viewer logic.

### Initialization

```javascript
import PlyPreviewSkill from './PlyPreviewSkill.js';

const viewer = new PlyPreviewSkill('container-id', {
    backgroundColor: 0x111111,
    pointSize: 0.05
});
```

### Methods

#### `loadModel(url, onProgress, onLoad, onError)`

Loads a PLY model from a URL.

- **url** (string): Path to the .ply file.
- **onProgress** (function): Callback `(percent) => {}`.
- **onLoad** (function): Callback `(geometry) => {}`.
- **onError** (function): Callback `(error) => {}`.

#### `dispose()`

Cleans up WebGL context and event listeners.

## Integration Example

```javascript
// In your main application script
const viewer = new PlyPreviewSkill('3d-viewer');

// Load a model
viewer.loadModel(
    '/api/download/model.ply',
    (percent) => console.log(`Loading: ${percent}%`),
    () => console.log('Loaded!'),
    (err) => console.error(err)
);
```

## Backend API

### Upload PLY
- **Endpoint**: `POST /api/upload`
- **Body**: `multipart/form-data` with `files` field.
- **Response**: JSON with `task_id`.

### Get Status
- **Endpoint**: `GET /api/status/<task_id>`
- **Response**: JSON with `status: "completed"` and `result: "<filename>"` if successful.

### Download/View
- **Endpoint**: `GET /api/download/<filename>`
- **Response**: The PLY file content.

## Testing

1.  **Upload**: Drag and drop a .ply file (ASCII or Binary).
2.  **Preview**: The model should appear in the viewer area.
3.  **Interaction**: Use mouse to rotate (Left Click), pan (Right Click), and zoom (Scroll).
4.  **Large Files**: Test with files up to 50MB.

## Browser Compatibility

- Chrome (Desktop/Mobile)
- Firefox
- Safari
- Edge

## Performance Notes

- **Vertex Colors**: Supported and enabled by default.
- **Point Size**: Adjustable via options.
- **Memory**: Large files (e.g., >100MB) may cause context loss on low-memory mobile devices.
