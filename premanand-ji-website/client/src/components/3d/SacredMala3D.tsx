import { useEffect, useRef } from "react";
import * as THREE from "three";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface SacredMala3DProps {
  className?: string;
}

export default function SacredMala3D({ className = "" }: SacredMala3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    let renderer: THREE.WebGLRenderer | null = null;
    try {
      renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      });
    } catch {
      return;
    }

    const width = container.clientWidth || 700;
    const height = container.clientHeight || 350;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 9.2);

    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffedd5, 1.2);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffa834, 2.5);
    dirLight1.position.set(5, 5, 5);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xe06015, 1.8);
    dirLight2.position.set(-5, -3, 3);
    scene.add(dirLight2);

    const centerPointLight = new THREE.PointLight(0xffb74d, 3, 10);
    centerPointLight.position.set(0, 0, 1);
    scene.add(centerPointLight);

    // Mala Root Group
    const malaRoot = new THREE.Group();
    malaRoot.rotation.x = 0.35; // gentle tilt toward viewer
    scene.add(malaRoot);

    // 108 Sacred Beads Path (Elliptical torus)
    const beadCount = 108;
    const radiusX = 4.6;
    const radiusY = 2.1;
    const waveAmp = 0.25;

    // Use InstancedMesh for the 108 beads for optimal 60fps performance
    const beadGeom = new THREE.SphereGeometry(0.11, 16, 16);
    const beadMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color("#c4782b"),
      roughness: 0.35,
      metalness: 0.2,
      emissive: new THREE.Color("#4a2106"),
      emissiveIntensity: 0.25,
    });

    const instancedBeads = new THREE.InstancedMesh(beadGeom, beadMat, beadCount);
    const dummy = new THREE.Object3D();
    const threadPoints: THREE.Vector3[] = [];

    for (let i = 0; i < beadCount; i++) {
      const theta = (i / beadCount) * Math.PI * 2;
      const x = Math.cos(theta) * radiusX;
      const y = Math.sin(theta) * radiusY;
      const z = Math.sin(theta * 4) * waveAmp;

      const pos = new THREE.Vector3(x, y, z);
      threadPoints.push(pos);

      dummy.position.copy(pos);
      dummy.scale.setScalar(1);
      dummy.updateMatrix();
      instancedBeads.setMatrixAt(i, dummy.matrix);
    }
    instancedBeads.instanceMatrix.needsUpdate = true;
    malaRoot.add(instancedBeads);

    // Connecting Sacred Thread (Sutra)
    threadPoints.push(threadPoints[0].clone()); // Close loop
    const threadGeom = new THREE.BufferGeometry().setFromPoints(threadPoints);
    const threadMat = new THREE.LineBasicMaterial({
      color: 0x9e5218,
      transparent: true,
      opacity: 0.45,
    });
    const threadLine = new THREE.Line(threadGeom, threadMat);
    malaRoot.add(threadLine);

    // Sumeru (Guru Bead) at the crown
    const sumeruGeom = new THREE.SphereGeometry(0.18, 20, 20);
    const sumeruMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color("#e59a3d"),
      roughness: 0.25,
      metalness: 0.4,
      emissive: new THREE.Color("#753508"),
      emissiveIntensity: 0.5,
    });
    const sumeruMesh = new THREE.Mesh(sumeruGeom, sumeruMat);
    sumeruMesh.position.set(0, radiusY + 0.05, 0);
    malaRoot.add(sumeruMesh);

    // Sumeru Spire / Bindu Cap
    const spireGeom = new THREE.ConeGeometry(0.08, 0.22, 12);
    const spireMat = new THREE.MeshBasicMaterial({ color: 0xffd580 });
    const spireMesh = new THREE.Mesh(spireGeom, spireMat);
    spireMesh.position.set(0, radiusY + 0.22, 0);
    spireMesh.rotation.z = Math.PI;
    malaRoot.add(spireMesh);

    // Mouse Tracking
    let targetMouseX = 0;
    let targetMouseY = 0;
    let currentMouseX = 0;
    let currentMouseY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      targetMouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      targetMouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    // Scroll scrub animation: mala rotates as user scrolls past #japa
    const scrollObj = { rotationOffset: 0 };
    const scrollAnim = gsap.to(scrollObj, {
      rotationOffset: Math.PI * 2,
      ease: "none",
      scrollTrigger: {
        trigger: "#japa",
        start: "top bottom",
        end: "bottom top",
        scrub: 0.5,
      },
    });

    // Resize Observer
    const handleResize = () => {
      if (!renderer || !container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    // Render Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const delta = Math.min(clock.getDelta(), 0.1);
      const elapsedTime = clock.getElapsedTime();

      currentMouseX += (targetMouseX - currentMouseX) * 0.05;
      currentMouseY += (targetMouseY - currentMouseY) * 0.05;

      // Slow idle rotation + continuous scroll turn
      malaRoot.rotation.z = elapsedTime * 0.12 + scrollObj.rotationOffset;
      malaRoot.rotation.x = 0.35 - currentMouseY * 0.25;
      malaRoot.rotation.y = currentMouseX * 0.3 + Math.sin(elapsedTime * 0.5) * 0.08;

      // Subtle breathing scale
      const breathe = 1 + Math.sin(elapsedTime * 1.5) * 0.015;
      malaRoot.scale.set(breathe, breathe, breathe);

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("mousemove", handleMouseMove);
      resizeObserver.disconnect();
      scrollAnim.kill();

      if (renderer && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
        renderer.dispose();
      }

      beadGeom.dispose();
      beadMat.dispose();
      threadGeom.dispose();
      threadMat.dispose();
      sumeruGeom.dispose();
      sumeruMat.dispose();
      spireGeom.dispose();
      spireMat.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className={`absolute inset-0 pointer-events-none z-0 flex items-center justify-center overflow-visible ${className}`}
      aria-hidden="true"
    />
  );
}
