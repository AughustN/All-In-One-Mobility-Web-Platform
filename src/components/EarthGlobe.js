import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

const EarthGlobe = ({ visible, onClose }) => {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const earthRef = useRef(null);
  const animationIdRef = useRef(null);

  useEffect(() => {
    console.log('🌍 EarthGlobe visible:', visible);
    if (!visible || !containerRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(
      45,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.z = 3;

    // Vietnam coordinates for zoom target
    const vietnamLat = 10.762622; // Ho Chi Minh City
    const vietnamLon = 106.660172;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true 
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 3, 5);
    scene.add(directionalLight);

    // Earth
    const geometry = new THREE.SphereGeometry(1, 64, 64);
    
    // Load Earth texture
    const textureLoader = new THREE.TextureLoader();
    const earthTexture = textureLoader.load(
      'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg',
      () => {
        console.log('Earth texture loaded');
      }
    );

    const material = new THREE.MeshPhongMaterial({
      map: earthTexture,
      bumpScale: 0.05,
    });

    const earth = new THREE.Mesh(geometry, material);
    scene.add(earth);
    earthRef.current = earth;

    // Stars background
    const starsGeometry = new THREE.BufferGeometry();
    const starsMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.7,
      transparent: true
    });

    const starsVertices = [];
    for (let i = 0; i < 10000; i++) {
      const x = (Math.random() - 0.5) * 2000;
      const y = (Math.random() - 0.5) * 2000;
      const z = (Math.random() - 0.5) * 2000;
      starsVertices.push(x, y, z);
    }

    starsGeometry.setAttribute(
      'position',
      new THREE.Float32BufferAttribute(starsVertices, 3)
    );

    const stars = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(stars);

    // Animation
    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);

      // Rotate Earth
      if (earthRef.current) {
        earthRef.current.rotation.y += 0.001;
      }

      // Rotate stars slowly
      stars.rotation.y += 0.0001;

      renderer.render(scene, camera);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    // Handle mouse wheel to zoom into Vietnam
    const handleWheel = (event) => {
      event.preventDefault();
      
      if (event.deltaY < 0) {
        // Scroll up = Zoom in to Vietnam
        console.log('🌍 Zooming into Vietnam...');
        
        // Animate camera zoom
        const targetZ = 1.5;
        const duration = 1000;
        const startZ = camera.position.z;
        const startTime = Date.now();
        
        const animateZoom = () => {
          const elapsed = Date.now() - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3); // Ease out
          
          camera.position.z = startZ - (startZ - targetZ) * eased;
          
          if (progress < 1) {
            requestAnimationFrame(animateZoom);
          } else {
            // Zoom complete, close Earth and show map
            setTimeout(() => {
              onClose();
            }, 500);
          }
        };
        
        animateZoom();
      }
    };

    window.addEventListener('resize', handleResize);
    containerRef.current.addEventListener('wheel', handleWheel, { passive: false });

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (containerRef.current) {
        containerRef.current.removeEventListener('wheel', handleWheel);
      }
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (containerRef.current && renderer.domElement) {
        containerRef.current.removeChild(renderer.domElement);
      }
      geometry.dispose();
      material.dispose();
      starsGeometry.dispose();
      starsMaterial.dispose();
      renderer.dispose();
    };
  }, [visible, onClose]);

  if (!visible) {
    console.log('🌍 EarthGlobe not visible, returning null');
    return null;
  }

  console.log('🌍 EarthGlobe rendering...');
  return (
    <div
      ref={containerRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 99999,
        background: 'linear-gradient(to bottom, #000000, #0a0a1a)',
        animation: 'fadeIn 0.5s ease-in',
        pointerEvents: 'auto'
      }}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          padding: '12px 24px',
          background: 'rgba(255, 255, 255, 0.1)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          borderRadius: '8px',
          color: 'white',
          fontSize: '14px',
          fontWeight: 500,
          cursor: 'pointer',
          backdropFilter: 'blur(10px)',
          transition: 'all 0.3s',
          zIndex: 10000
        }}
        onMouseEnter={(e) => {
          e.target.style.background = 'rgba(255, 255, 255, 0.2)';
          e.target.style.transform = 'scale(1.05)';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = 'rgba(255, 255, 255, 0.1)';
          e.target.style.transform = 'scale(1)';
        }}
      >
        Quay lại bản đồ
      </button>

      {/* Info text */}
      {/* <div
        style={{
          position: 'absolute',
          bottom: '80px',
          left: '50%',
          transform: 'translateX(-50%)',
          color: 'white',
          fontSize: '18px',
          fontWeight: 300,
          textAlign: 'center',
          opacity: 0.8,
          animation: 'fadeIn 1s ease-in 0.5s both'
        }}
      >
        🌍 Trái Đất - Hành tinh xanh của chúng ta
      </div> */}

      {/* Scroll hint */}
      <div
        style={{
          position: 'absolute',
          bottom: '40px',
          left: '50%',
          transform: 'translateX(-50%)',
          color: 'rgba(255, 255, 255, 0.6)',
          fontSize: '14px',
          fontWeight: 300,
          textAlign: 'center',
          animation: 'fadeIn 1s ease-in 1s both, bounce 2s ease-in-out 2s infinite'
        }}
      >
        ⬆️ Cuộn chuột để zoom vào Việt Nam
      </div>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        
        @keyframes bounce {
          0%, 100% {
            transform: translateX(-50%) translateY(0);
          }
          50% {
            transform: translateX(-50%) translateY(-10px);
          }
        }
      `}</style>
    </div>
  );
};

export default EarthGlobe;
