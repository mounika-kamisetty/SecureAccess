/**
 * SecureAssess - Three.js Landing Page Scene
 */

let scene, camera, renderer, particles, shieldGroup;
let mouseX = 0;
let mouseY = 0;
let targetX = 0;
let targetY = 0;
const windowHalfX = window.innerWidth / 2;
const windowHalfY = window.innerHeight / 2;

export function initHeroScene() {
    const container = document.getElementById('canvas-container');
    if (!container || !window.THREE) return;

    // 1. Setup Scene & Camera
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0f172a, 0.001); // matches slate-900

    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    // Position camera so shield is on the right
    camera.position.z = 20;
    camera.position.x = window.innerWidth > 1024 ? -5 : 0; // shift for text

    // 2. Setup Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    // 3. Create Objects
    shieldGroup = new THREE.Group();
    // Shift shield to the right for large screens
    shieldGroup.position.x = window.innerWidth > 1024 ? 10 : 0;
    scene.add(shieldGroup);

    createSecurityShield();
    createParticles();
    createNetworkLines();

    // 4. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x4f46e5, 1, 50); // Indigo glow
    pointLight.position.set(5, 5, 5);
    shieldGroup.add(pointLight);
    
    const pointLight2 = new THREE.PointLight(0x06b6d4, 1, 50); // Cyan glow
    pointLight2.position.set(-5, -5, 5);
    shieldGroup.add(pointLight2);

    // 5. Events
    document.addEventListener('mousemove', handleMouseMovement, false);
    window.addEventListener('resize', onWindowResize, false);
    
    // Handle visibility to save battery/CPU
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            cancelAnimationFrame(animationId);
        } else {
            animateScene();
        }
    });

    animateScene();
}

function createSecurityShield() {
    // Outer Ring
    const geometryOuter = new THREE.TorusGeometry(6, 0.1, 16, 100);
    const materialOuter = new THREE.MeshBasicMaterial({ color: 0x4f46e5, transparent: true, opacity: 0.3 });
    const ring1 = new THREE.Mesh(geometryOuter, materialOuter);
    shieldGroup.add(ring1);

    // Inner Ring
    const geometryInner = new THREE.TorusGeometry(4.5, 0.05, 16, 100);
    const materialInner = new THREE.MeshBasicMaterial({ color: 0x06b6d4, transparent: true, opacity: 0.5 });
    const ring2 = new THREE.Mesh(geometryInner, materialInner);
    ring2.rotation.x = Math.PI / 2;
    shieldGroup.add(ring2);

    // Core shape (Icosahedron representing data/shield)
    const geoCore = new THREE.IcosahedronGeometry(3, 1);
    const matCore = new THREE.MeshPhongMaterial({ 
        color: 0x1e293b, 
        emissive: 0x0f172a,
        wireframe: true,
        transparent: true,
        opacity: 0.8
    });
    const core = new THREE.Mesh(geoCore, matCore);
    shieldGroup.add(core);
    
    // Add glowing core center
    const geoCenter = new THREE.SphereGeometry(1.5, 32, 32);
    const matCenter = new THREE.MeshBasicMaterial({ color: 0x4f46e5, transparent: true, opacity: 0.8 });
    const center = new THREE.Mesh(geoCenter, matCenter);
    shieldGroup.add(center);
}

function createParticles() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    
    // Create 300 floating particles
    for (let i = 0; i < 300; i++) {
        const x = (Math.random() - 0.5) * 60;
        const y = (Math.random() - 0.5) * 60;
        const z = (Math.random() - 0.5) * 60 - 10;
        vertices.push(x, y, z);
    }

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    
    const material = new THREE.PointsMaterial({ 
        color: 0x38bdf8, // light blue
        size: 0.1,
        transparent: true,
        opacity: 0.6
    });
    
    particles = new THREE.Points(geometry, material);
    scene.add(particles);
}

function createNetworkLines() {
    // A simplified visual network around the shield
    const material = new THREE.LineBasicMaterial({
        color: 0x6366f1,
        transparent: true,
        opacity: 0.2
    });

    const points = [];
    for(let i=0; i<15; i++) {
        points.push(new THREE.Vector3(
            (Math.random() - 0.5) * 20,
            (Math.random() - 0.5) * 20,
            (Math.random() - 0.5) * 10
        ));
    }
    
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const line = new THREE.Line(geometry, material);
    shieldGroup.add(line);
}

function handleMouseMovement(event) {
    mouseX = (event.clientX - windowHalfX) * 0.001;
    mouseY = (event.clientY - windowHalfY) * 0.001;
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    
    // Update shield position on resize
    if(shieldGroup) {
        shieldGroup.position.x = window.innerWidth > 1024 ? 10 : 0;
        camera.position.x = window.innerWidth > 1024 ? -5 : 0;
    }
}

let animationId;
function animateScene() {
    animationId = requestAnimationFrame(animateScene);

    // Interpolate mouse movement for smooth rotation
    targetX = mouseX * 2;
    targetY = mouseY * 2;
    
    if (shieldGroup) {
        shieldGroup.rotation.y += 0.005 + (targetX - shieldGroup.rotation.y) * 0.05;
        shieldGroup.rotation.x += 0.002 + (targetY - shieldGroup.rotation.x) * 0.05;
        
        // Internal animations
        shieldGroup.children[0].rotation.z -= 0.002; // outer ring
        shieldGroup.children[1].rotation.z += 0.005; // inner ring
        shieldGroup.children[2].rotation.y += 0.001; // icosahedron
        
        // Gentle bobbing
        shieldGroup.position.y = Math.sin(Date.now() * 0.001) * 0.5;
    }
    
    if (particles) {
        particles.rotation.y += 0.0005;
    }

    renderer.render(scene, camera);
}

// Auto-init if we're on a page with the canvas
if (document.getElementById('canvas-container')) {
    initHeroScene();
}
