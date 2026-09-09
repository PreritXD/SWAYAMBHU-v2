import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * ThreeCanvas
 * Pure Three.js WebGL canvas rendering a mathematically precise, interactive 3D sacred
 * geometric medallion (Vrindavan architectural mandala disc using TorusGeometry, CylinderGeometry,
 * and RingGeometry in brushed gold & saffron wireframe/solid duality).
 * Strictly zero particle swarms, zero shader-blob distortions, with smooth lerped mouse-follow inertia.
 */
export default function ThreeCanvas() {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Scene Setup
    const scene = new THREE.Scene();

    // 2. Camera Setup
    const width = container.clientWidth || 480;
    const height = container.clientHeight || 480;
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 8);

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.appendChild(renderer.domElement);

    // 4. Crisp Directional Lighting
    // Warm Gold Primary Key Light
    const keyLight = new THREE.DirectionalLight(0xF59E0B, 2.2);
    keyLight.position.set(5, 8, 5);
    scene.add(keyLight);

    // Saffron Accent Light
    const saffronLight = new THREE.DirectionalLight(0xE65100, 1.8);
    saffronLight.position.set(-6, -4, 4);
    scene.add(saffronLight);

    // Neutral Clean Rim Light
    const rimLight = new THREE.DirectionalLight(0xFFFFFF, 1.4);
    rimLight.position.set(0, 5, -5);
    scene.add(rimLight);

    // Soft Ambient Foundation
    const ambientLight = new THREE.AmbientLight(0xFAF8F5, 0.9);
    scene.add(ambientLight);

    // 5. Materials (Brushed Gold & Saffron Wireframe / Solid Duality)
    const goldSolidMat = new THREE.MeshStandardMaterial({
      color: 0xD97706,
      metalness: 0.45,
      roughness: 0.28
    });

    const saffronSolidMat = new THREE.MeshStandardMaterial({
      color: 0xE65100,
      metalness: 0.4,
      roughness: 0.32
    });

    const goldWireMat = new THREE.MeshStandardMaterial({
      color: 0xF59E0B,
      wireframe: true,
      metalness: 0.5,
      roughness: 0.25
    });

    const ivoryAccentMat = new THREE.MeshStandardMaterial({
      color: 0xFFFDF5,
      metalness: 0.2,
      roughness: 0.4
    });

    // 6. Procedural Mandala Medallion Geometry Group
    const mandalaGroup = new THREE.Group();

    // Outer Sanctum Ring (Golden Torus)
    const outerRingGeo = new THREE.TorusGeometry(2.4, 0.05, 16, 100);
    const outerRingMesh = new THREE.Mesh(outerRingGeo, goldSolidMat);
    mandalaGroup.add(outerRingMesh);

    // Outer Wireframe Harmonic Halo
    const haloRingGeo = new THREE.TorusGeometry(2.55, 0.02, 12, 80);
    const haloRingMesh = new THREE.Mesh(haloRingGeo, goldWireMat);
    mandalaGroup.add(haloRingMesh);

    // 12-Spoke Wheel of Dharma & Devotional Hours (Cylinders)
    const spokeCount = 12;
    for (let i = 0; i < spokeCount; i++) {
      const angle = (i / spokeCount) * Math.PI * 2;
      const spokeGeo = new THREE.CylinderGeometry(0.025, 0.025, 2.35, 12);
      const spokeMesh = new THREE.Mesh(spokeGeo, i % 2 === 0 ? saffronSolidMat : goldSolidMat);
      spokeMesh.position.set(Math.cos(angle) * 1.18, Math.sin(angle) * 1.18, 0);
      spokeMesh.rotation.z = angle + Math.PI / 2;
      mandalaGroup.add(spokeMesh);
    }

    // Concentric Inner Petal Disk (Ring Geometry)
    const midRingGeo = new THREE.RingGeometry(1.25, 1.45, 64);
    const midRingMesh = new THREE.Mesh(midRingGeo, goldSolidMat);
    mandalaGroup.add(midRingMesh);

    const midWireGeo = new THREE.RingGeometry(1.48, 1.55, 48);
    const midWireMesh = new THREE.Mesh(midWireGeo, goldWireMat);
    mandalaGroup.add(midWireMesh);

    // Inner 8-Petal Sacred Lotus Node
    const petalCount = 8;
    for (let i = 0; i < petalCount; i++) {
      const angle = (i / petalCount) * Math.PI * 2;
      const petalTorus = new THREE.TorusGeometry(0.5, 0.035, 12, 36);
      const petalMesh = new THREE.Mesh(petalTorus, saffronSolidMat);
      petalMesh.position.set(Math.cos(angle) * 0.7, Math.sin(angle) * 0.7, 0.06);
      petalMesh.rotation.z = angle;
      mandalaGroup.add(petalMesh);
    }

    // Central Bindu / Lotus Core (Beveled Cylinder & Inner Sphere)
    const centerCoreGeo = new THREE.CylinderGeometry(0.32, 0.32, 0.12, 32);
    const centerCoreMesh = new THREE.Mesh(centerCoreGeo, ivoryAccentMat);
    centerCoreMesh.rotation.x = Math.PI / 2;
    mandalaGroup.add(centerCoreMesh);

    const centerBinduGeo = new THREE.SphereGeometry(0.18, 24, 24);
    const centerBinduMesh = new THREE.Mesh(centerBinduGeo, saffronSolidMat);
    centerBinduMesh.position.z = 0.1;
    mandalaGroup.add(centerBinduMesh);

    // Add Mandala to Scene
    scene.add(mandalaGroup);

    // 7. Mouse-Follow Inertia & Interaction Handling
    let mouseX = 0;
    let mouseY = 0;
    let targetRotationX = 0;
    let targetRotationY = 0;

    const handleMouseMove = (event) => {
      const rect = container.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
      mouseX = x;
      mouseY = y;
      targetRotationY = mouseX * 0.55;
      targetRotationX = -mouseY * 0.55;
    };

    const handleMouseLeave = () => {
      targetRotationX = 0;
      targetRotationY = 0;
    };

    window.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('mouseleave', handleMouseLeave);

    // 8. Resize Observer
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    // 9. 60FPS Render Loop with Lerp & Constant Subtle Cosmic Drift
    let animationFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();

      // Continuous subtle devotional rotation
      mandalaGroup.rotation.z += delta * 0.12;

      // Smooth lerp toward mouse target (damping factor 0.05)
      mandalaGroup.rotation.x += (targetRotationX - mandalaGroup.rotation.x) * 0.05;
      mandalaGroup.rotation.y += (targetRotationY - mandalaGroup.rotation.y) * 0.05;

      renderer.render(scene, camera);
    };

    animate();

    // 10. Clean Cleanup Lifecycle
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('mouseleave', handleMouseLeave);
      resizeObserver.disconnect();

      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }

      // Dispose Geometries and Materials
      mandalaGroup.traverse((obj) => {
        if (obj.isMesh) {
          obj.geometry.dispose();
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => m.dispose());
          } else {
            obj.material.dispose();
          }
        }
      });
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        minHeight: "360px",
        aspectRatio: "1 / 1",
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        touchAction: "none",
        cursor: "grab",
        userSelect: "none"
      }}
      title="श्री राधा केली कुंज • पवित्र यंत्र एवं आध्यात्मिक मंडल (Drag to interact)"
    />
  );
}
