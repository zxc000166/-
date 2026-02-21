import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';

export default class PlyPreviewSkill {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container element with id '${containerId}' not found.`);
            return;
        }

        this.options = {
            backgroundColor: 0x111111,
            pointSize: 0.05,
            ...options
        };

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.model = null;
        this.animationId = null;

        this.init();
    }

    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.backgroundColor);

        // Camera
        this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.camera.position.z = 5;

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.innerHTML = ''; // Clear previous canvas if any
        this.container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(1, 1, 1).normalize();
        this.scene.add(directionalLight);

        // Grid Helper
        const gridHelper = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
        this.scene.add(gridHelper);

        // Resize Listener
        window.addEventListener('resize', this.onWindowResize.bind(this), false);

        // Start Loop
        this.animate();
    }

    onWindowResize() {
        if (!this.camera || !this.renderer) return;
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    animate() {
        this.animationId = requestAnimationFrame(this.animate.bind(this));
        if (this.controls) this.controls.update();
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    loadModel(url, onProgress, onLoad, onError) {
        // Dispose existing model
        if (this.model) {
            this.scene.remove(this.model);
            if (this.model.geometry) this.model.geometry.dispose();
            if (this.model.material) this.model.material.dispose();
            this.model = null;
        }

        const loader = new PLYLoader();
        loader.load(
            url,
            (geometry) => {
                // Compute Normals if missing
                if (!geometry.attributes.normal) {
                    geometry.computeVertexNormals();
                }

                // Center and Scale
                geometry.computeBoundingBox();
                const center = geometry.boundingBox.getCenter(new THREE.Vector3());
                geometry.translate(-center.x, -center.y, -center.z);

                const size = geometry.boundingBox.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                const scale = 3 / maxDim; // Fit within a reasonable view
                geometry.scale(scale, scale, scale);

                // Create Material
                // Check if vertex colors exist
                const materialOptions = {
                    size: this.options.pointSize,
                    vertexColors: geometry.attributes.color ? true : false
                };

                // Create Mesh or Points
                // If it has faces (index attribute), it's a mesh. Otherwise, points.
                if (geometry.index) {
                     materialOptions.flatShading = true; // Better for low-poly
                     materialOptions.side = THREE.DoubleSide;
                     const material = new THREE.MeshStandardMaterial(materialOptions);
                     // If no vertex colors, use a default color
                     if (!materialOptions.vertexColors) material.color.setHex(0x00ffff);
                     
                     this.model = new THREE.Mesh(geometry, material);
                } else {
                     const material = new THREE.PointsMaterial(materialOptions);
                     // If no vertex colors, use a default color
                     if (!materialOptions.vertexColors) material.color.setHex(0x00ffff);
                     
                     this.model = new THREE.Points(geometry, material);
                }

                this.scene.add(this.model);

                if (onLoad) onLoad(geometry);
            },
            (xhr) => {
                if (onProgress) {
                    const percent = (xhr.loaded / xhr.total) * 100;
                    onProgress(percent);
                }
            },
            (error) => {
                console.error('An error happened loading the PLY model:', error);
                if (onError) onError(error);
            }
        );
    }

    dispose() {
        cancelAnimationFrame(this.animationId);
        window.removeEventListener('resize', this.onWindowResize.bind(this));
        
        if (this.renderer) {
            this.renderer.dispose();
            this.container.innerHTML = '';
        }
        
        if (this.model) {
            if (this.model.geometry) this.model.geometry.dispose();
            if (this.model.material) this.model.material.dispose();
        }
    }
}
