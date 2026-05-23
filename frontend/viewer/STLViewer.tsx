'use client';

import { Suspense, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, useLoader } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import * as THREE from 'three';

interface STLViewerProps {
  url: string;
}

function STLModel({ url }: { url: string }) {
  const geometry = useLoader(STLLoader, url);
  const meshRef = useRef<THREE.Mesh>(null);

  geometry.computeBoundingBox();
  const center = new THREE.Vector3();
  geometry.boundingBox?.getCenter(center);
  geometry.translate(-center.x, -center.y, -center.z);

  return (
    <mesh ref={meshRef} geometry={geometry}>
      <meshStandardMaterial color="#00d4ff" metalness={0.6} roughness={0.3} />
    </mesh>
  );
}

function LoadingFallback() {
  return (
    <mesh>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="#1e293b" wireframe />
    </mesh>
  );
}

export default function STLViewer({ url }: STLViewerProps) {
  return (
    <Canvas
      camera={{ position: [50, 50, 50], fov: 50 }}
      style={{ background: '#0a0e17' }}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 10, 10]} intensity={0.8} />
      <directionalLight position={[-10, -10, -10]} intensity={0.3} />
      <pointLight position={[0, 50, 0]} intensity={0.5} color="#00d4ff" />

      <Suspense fallback={<LoadingFallback />}>
        <STLModel url={url} />
      </Suspense>

      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        rotateSpeed={0.5}
        zoomSpeed={0.8}
      />

      <gridHelper args={[200, 20, '#1e293b', '#0f172a']} />
    </Canvas>
  );
}
