import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

interface DivineLotus3DProps {
  className?: string;
}

export default function DivineLotus3D({ className = "" }: DivineLotus3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [hasWebGL, setHasWebGL] = useState(true);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // Check if WebGL is available
    let renderer: THREE.WebGLRenderer | null = null;
    try {
      renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      });
    } catch {
      setHasWebGL(false);
      return;
    }

    const width = container.clientWidth || 500;
    const height = container.clientHeight || 500;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 2.5, 9.5);
    camera.lookAt(0, 0, 0);

    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.appendChild(renderer.domElement);

    // --- Lighting ---
    const ambientLight = new THREE.AmbientLight(0xfff1db, 1.4);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffd18a, 2.6);
    keyLight.position.set(6, 10, 8);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0xe86928, 2.2);
    rimLight.position.set(-6, -3, -4);
    scene.add(rimLight);

    // Center lotus spiritual glow
    const coreLight = new THREE.PointLight(0xffaa33, 4.5, 12);
    coreLight.position.set(0, 0.4, 0);
    scene.add(coreLight);

    // --- Root Lotus Group ---
    const lotusRoot = new THREE.Group();
    lotusRoot.position.set(0, -0.4, 0);
    lotusRoot.rotation.x = 0.55; // Tilt toward camera for majestic view
    scene.add(lotusRoot);

    // Helper: Create a curved procedural petal geometry
    const createPetalGeometry = (width: number, length: number, cupping: number, tipCurl: number) => {
      const segW = 14;
      const segL = 20;
      const geom = new THREE.PlaneGeometry(width, length, segW, segL);
      const pos = geom.attributes.position;

      for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i);
        const y = pos.getY(i);
        // Normalize coordinates: v goes from 0 (base) to 1 (tip)
        const v = (y + length / 2) / length;
        const u = x / (width / 2); // -1 to 1

        // Lotus petal outline shape: pointed at tip and tapered at base, widest around v = 0.4
        const widthFactor = Math.sin(v * Math.PI) * (1 - v * 0.25);
        const newX = u * (width / 2) * widthFactor;

        // Cupping curve (cross section) + longitudinal curl
        const cupZ = -Math.cos(u * (Math.PI / 2)) * cupping * Math.sin(v * Math.PI);
        const curlZ = Math.sin(v * Math.PI * 0.8) * tipCurl - Math.pow(v, 2.5) * (tipCurl * 1.5);

        pos.setXYZ(i, newX, y + length / 2, cupZ + curlZ);
      }

      geom.computeVertexNormals();
      return geom;
    };

    // Petal materials with golden-saffron gradient feel
    const outerPetalMaterial = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color("#e67c2e"),
      emissive: new THREE.Color("#5f2104"),
      emissiveIntensity: 0.35,
      roughness: 0.38,
      metalness: 0.12,
      clearcoat: 0.4,
      clearcoatRoughness: 0.25,
      side: THREE.DoubleSide,
    });

    const midPetalMaterial = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color("#f1973b"),
      emissive: new THREE.Color("#7a2f07"),
      emissiveIntensity: 0.45,
      roughness: 0.32,
      metalness: 0.1,
      clearcoat: 0.5,
      side: THREE.DoubleSide,
    });

    const innerPetalMaterial = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color("#fdbd5e"),
      emissive: new THREE.Color("#9e450b"),
      emissiveIntensity: 0.6,
      roughness: 0.28,
      metalness: 0.08,
      clearcoat: 0.6,
      side: THREE.DoubleSide,
    });

    // Petal groups to allow dynamic blooming via scroll
    const outerTierGroup = new THREE.Group();
    const midTierGroup = new THREE.Group();
    const innerTierGroup = new THREE.Group();
    lotusRoot.add(outerTierGroup);
    lotusRoot.add(midTierGroup);
    lotusRoot.add(innerTierGroup);

    // Tier 1: Outer Petals (12 petals, open & majestic)
    const outerGeom = createPetalGeometry(1.65, 3.4, 0.45, 0.7);
    const outerCount = 12;
    for (let i = 0; i < outerCount; i++) {
      const angle = (i / outerCount) * Math.PI * 2;
      const petalMesh = new THREE.Mesh(outerGeom, outerPetalMaterial);
      petalMesh.rotation.y = angle;
      petalMesh.rotation.z = -0.92; // unfurled angle
      petalMesh.position.y = -0.15;
      outerTierGroup.add(petalMesh);
    }

    // Tier 2: Mid Petals (10 petals, offset)
    const midGeom = createPetalGeometry(1.4, 2.9, 0.5, 0.55);
    const midCount = 10;
    for (let i = 0; i < midCount; i++) {
      const angle = (i / midCount) * Math.PI * 2 + Math.PI / midCount;
      const petalMesh = new THREE.Mesh(midGeom, midPetalMaterial);
      petalMesh.rotation.y = angle;
      petalMesh.rotation.z = -0.68;
      petalMesh.position.y = 0.05;
      midTierGroup.add(petalMesh);
    }

    // Tier 3: Inner Petals (8 petals, gently cupping the center)
    const innerGeom = createPetalGeometry(1.15, 2.2, 0.55, 0.35);
    const innerCount = 8;
    for (let i = 0; i < innerCount; i++) {
      const angle = (i / innerCount) * Math.PI * 2 + (Math.PI / innerCount) * 0.5;
      const petalMesh = new THREE.Mesh(innerGeom, innerPetalMaterial);
      petalMesh.rotation.y = angle;
      petalMesh.rotation.z = -0.42;
      petalMesh.position.y = 0.18;
      innerTierGroup.add(petalMesh);
    }

    // Central Seedpod (Karnika)
    const seedpodGeom = new THREE.CylinderGeometry(0.72, 0.45, 0.5, 24);
    const seedpodMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color("#df932e"),
      roughness: 0.4,
      metalness: 0.3,
      emissive: new THREE.Color("#4a2107"),
      emissiveIntensity: 0.3,
    });
    const seedpod = new THREE.Mesh(seedpodGeom, seedpodMat);
    seedpod.position.y = 0.15;
    lotusRoot.add(seedpod);

    // Golden Stamens (Filaments around seedpod)
    const stamenCount = 36;
    const stamenGroup = new THREE.Group();
    const stamenGeom = new THREE.CylinderGeometry(0.02, 0.02, 0.45, 6);
    const stamenTipGeom = new THREE.SphereGeometry(0.05, 8, 8);
    const stamenMat = new THREE.MeshBasicMaterial({ color: 0xffe28a });

    for (let i = 0; i < stamenCount; i++) {
      const angle = (i / stamenCount) * Math.PI * 2;
      const radius = 0.72;
      const stamenMesh = new THREE.Mesh(stamenGeom, stamenMat);
      const tipMesh = new THREE.Mesh(stamenTipGeom, stamenMat);
      stamenMesh.position.set(Math.cos(angle) * radius, 0.35, Math.sin(angle) * radius);
      stamenMesh.rotation.z = -Math.cos(angle) * 0.35;
      stamenMesh.rotation.x = Math.sin(angle) * 0.35;
      tipMesh.position.set(
        Math.cos(angle) * (radius + 0.08),
        0.58,
        Math.sin(angle) * (radius + 0.08)
      );
      stamenGroup.add(stamenMesh);
      stamenGroup.add(tipMesh);
    }
    lotusRoot.add(stamenGroup);

    // Sacred Aura Geometry: Luminous Golden Orbit Rings
    const ringGroup = new THREE.Group();
    const ringMat = new THREE.LineBasicMaterial({
      color: 0xefa148,
      transparent: true,
      opacity: 0.42,
    });

    const createAuraRing = (radius: number, segments: number) => {
      const pts = [];
      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        pts.push(new THREE.Vector3(Math.cos(theta) * radius, 0, Math.sin(theta) * radius));
      }
      const geom = new THREE.BufferGeometry().setFromPoints(pts);
      return new THREE.Line(geom, ringMat);
    };

    const ring1 = createAuraRing(3.8, 64);
    const ring2 = createAuraRing(4.5, 64);
    ring2.rotation.x = 0.25;
    ringGroup.add(ring1);
    ringGroup.add(ring2);
    ringGroup.position.y = -0.3;
    lotusRoot.add(ringGroup);

    // Subtle Halo Dust Particles around Lotus
    const haloDustCount = 80;
    const haloDustGeom = new THREE.BufferGeometry();
    const haloDustPos = new Float32Array(haloDustCount * 3);
    for (let i = 0; i < haloDustCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = 2.0 + Math.random() * 3.0;
      const height = (Math.random() - 0.5) * 2.2;
      haloDustPos[i * 3] = Math.cos(angle) * dist;
      haloDustPos[i * 3 + 1] = height;
      haloDustPos[i * 3 + 2] = Math.sin(angle) * dist;
    }
    haloDustGeom.setAttribute("position", new THREE.BufferAttribute(haloDustPos, 3));
    const haloDustMat = new THREE.PointsMaterial({
      color: 0xffd993,
      size: 0.12,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
    });
    const haloDust = new THREE.Points(haloDustGeom, haloDustMat);
    lotusRoot.add(haloDust);

    // --- Interactive Mouse Parallax ---
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const relX = (e.clientX - rect.left) / rect.width - 0.5;
      const relY = (e.clientY - rect.top) / rect.height - 0.5;
      targetMouseX = relX * 2;
      targetMouseY = relY * 2;
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    // --- GSAP ScrollTrigger Integration ---
    // As user scrolls past the hero section, the lotus tilts, expands, blooms, and spins into depth
    const scrollObj = {
      bloom: 0,
      rotationY: 0,
      scrollFade: 1,
      scale: 1,
    };

    const scrollAnim = gsap.to(scrollObj, {
      bloom: 0.28,
      rotationY: Math.PI * 0.9,
      scale: 1.15,
      ease: "power2.out",
      scrollTrigger: {
        trigger: ".hero-section",
        start: "top top",
        end: "bottom top",
        scrub: 0.8,
      },
      onUpdate: () => {
        // Unfurl petals with scroll
        outerTierGroup.children.forEach((child) => {
          child.rotation.z = -0.92 - scrollObj.bloom * 0.35;
        });
        midTierGroup.children.forEach((child) => {
          child.rotation.z = -0.68 - scrollObj.bloom * 0.3;
        });
        innerTierGroup.children.forEach((child) => {
          child.rotation.z = -0.42 - scrollObj.bloom * 0.25;
        });
      },
    });

    // Handle container resize
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

    // --- Animation Loop ---
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();

      // Lerp mouse
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Gentle natural hovering oscillation
      lotusRoot.position.y = -0.4 + Math.sin(elapsedTime * 1.2) * 0.12;
      lotusRoot.position.x = Math.cos(elapsedTime * 0.8) * 0.06;

      // Combine idle rotation, mouse parallax, and scroll scrub rotation
      lotusRoot.rotation.y = elapsedTime * 0.25 + mouseX * 0.5 + scrollObj.rotationY;
      lotusRoot.rotation.x = 0.55 - mouseY * 0.35 + Math.sin(elapsedTime * 0.9) * 0.04;
      lotusRoot.rotation.z = Math.sin(elapsedTime * 0.7) * 0.05 - mouseX * 0.2;

      // Aura rings counter-rotate
      ringGroup.rotation.y = -elapsedTime * 0.35;
      haloDust.rotation.y = elapsedTime * 0.15;

      // Pulse core light
      coreLight.intensity = 4.2 + Math.sin(elapsedTime * 3.0) * 0.8;

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

      // Dispose geometries & materials
      outerGeom.dispose();
      midGeom.dispose();
      innerGeom.dispose();
      seedpodGeom.dispose();
      stamenGeom.dispose();
      stamenTipGeom.dispose();
      haloDustGeom.dispose();
      outerPetalMaterial.dispose();
      midPetalMaterial.dispose();
      innerPetalMaterial.dispose();
      seedpodMat.dispose();
      stamenMat.dispose();
      ringMat.dispose();
      haloDustMat.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className={`relative w-full h-full flex items-center justify-center ${className}`}
      style={{ minHeight: "420px" }}
    >
      {!hasWebGL && (
        <img
          className="hero-art w-full h-full object-contain"
          src="/hero-lotus.png"
          alt="A luminous saffron lotus"
        />
      )}
    </div>
  );
}
