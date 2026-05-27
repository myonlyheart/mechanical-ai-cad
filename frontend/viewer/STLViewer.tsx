'use client';

import { Suspense, useRef } from 'react';
import { Canvas, useLoader } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import * as THREE from 'three';

interface STLViewerProps {
  url: string;
}

interface PartData {
  name: string;
  url: string;
  color?: string;
  position?: [number, number, number];
  visible?: boolean;
}

interface MultiPartViewerProps {
  parts: PartData[];
  selectedName?: string | null;
  onSelectPart?: (name: string) => void;
}

function STLModel({ url, color = '#00d4ff', position }: { url: string; color?: string; position?: [number, number, number] }) {
  const geometry = useLoader(STLLoader, url);
  const meshRef = useRef<THREE.Mesh>(null);

  geometry.computeBoundingBox();
  const center = new THREE.Vector3();
  geometry.boundingBox?.getCenter(center);
  geometry.translate(-center.x, -center.y, -center.z);

  return (
    <mesh ref={meshRef} geometry={geometry} position={position}>
      <meshStandardMaterial color={color} metalness={0.6} roughness={0.3} />
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

const PART_COLORS = ['#00d4ff', '#ff6b6b', '#4ecdc4', '#ffd93d', '#6bcb77', '#9b59b6'];

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

export function MultiPartViewer({ parts, selectedName, onSelectPart }: MultiPartViewerProps) {
  const visibleParts = parts.filter((p) => p.visible !== false);

  return (
    <Canvas
      camera={{ position: [100, 100, 100], fov: 50 }}
      style={{ background: '#0a0e17' }}
      onPointerMissed={() => onSelectPart?.('')}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 10, 10]} intensity={0.8} />
      <directionalLight position={[-10, -10, -10]} intensity={0.3} />
      <pointLight position={[0, 50, 0]} intensity={0.5} color="#00d4ff" />

      <Suspense fallback={<LoadingFallback />}>
        {visibleParts.map((part, i) => (
          <group
            key={part.name}
            onClick={(e) => {
              e.stopPropagation();
              onSelectPart?.(part.name);
            }}
          >
            <STLModel
              url={part.url}
              color={
                selectedName === part.name
                  ? '#ffffff'
                  : part.color || PART_COLORS[i % PART_COLORS.length]
              }
              position={part.position}
            />
          </group>
        ))}
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
