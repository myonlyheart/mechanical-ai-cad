'use client';

import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface AnchorData {
  id: string;
  name: string;
  type: string;
  position: [number, number, number];
  direction: [number, number, number];
  metadata?: Record<string, any>;
}

interface AnchorVisualizerProps {
  anchors: AnchorData[];
  visible?: boolean;
  highlightName?: string | null;
}

const ANCHOR_COLORS: Record<string, string> = {
  point: '#ff6b6b',
  face: '#4ecdc4',
  edge: '#ffd93d',
  axis: '#6bcb77',
  hole_center: '#9b59b6',
};

function AnchorPoint({
  anchor,
  highlight,
}: {
  anchor: AnchorData;
  highlight: boolean;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const color = ANCHOR_COLORS[anchor.type] || '#ffffff';
  const scale = highlight || hovered ? 1.5 : 1.0;

  useFrame(() => {
    if (meshRef.current) {
      const target = new THREE.Vector3(scale, scale, scale);
      meshRef.current.scale.lerp(target, 0.1);
    }
  });

  const dir = new THREE.Vector3(...anchor.direction).normalize();

  return (
    <group position={anchor.position}>
      {/* Anchor sphere */}
      <mesh
        ref={meshRef}
        onPointerEnter={() => setHovered(true)}
        onPointerLeave={() => setHovered(false)}
      >
        <sphereGeometry args={[1.5, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={highlight || hovered ? 0.8 : 0.3}
          transparent
          opacity={0.9}
        />
      </mesh>

      {/* Direction arrow */}
      <arrowHelper
        args={[dir, new THREE.Vector3(0, 0, 0), 10, color as any, 3, 2]}
      />

      {/* Label on hover */}
      {(hovered || highlight) && (
        <sprite position={[0, 8, 0]} scale={[20, 5, 1]}>
          <spriteMaterial color={color} transparent opacity={0.8} />
        </sprite>
      )}
    </group>
  );
}

export default function AnchorVisualizer({
  anchors,
  visible = true,
  highlightName,
}: AnchorVisualizerProps) {
  if (!visible || anchors.length === 0) return null;

  return (
    <group>
      {anchors.map((anchor) => (
        <AnchorPoint
          key={anchor.id}
          anchor={anchor}
          highlight={highlightName === anchor.name}
        />
      ))}
    </group>
  );
}

// Sidebar component for anchor list
export function AnchorList({
  anchors,
  selectedName,
  onSelect,
}: {
  anchors: AnchorData[];
  selectedName?: string | null;
  onSelect?: (name: string) => void;
}) {
  if (anchors.length === 0) {
    return (
      <div className="p-3 text-sm text-cad-muted">此零件无锚点</div>
    );
  }

  return (
    <div className="bg-cad-panel border border-cad-border rounded-xl overflow-hidden">
      <div className="p-3 border-b border-cad-border">
        <h3 className="text-sm font-semibold text-cad-text">锚点</h3>
      </div>
      <div className="p-2 space-y-1 max-h-48 overflow-y-auto">
        {anchors.map((anchor) => (
          <button
            key={anchor.id}
            onClick={() => onSelect?.(anchor.name)}
            className={`w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors ${
              selectedName === anchor.name
                ? 'bg-cad-accent/20 text-cad-accent'
                : 'hover:bg-cad-dark text-cad-text/80'
            }`}
          >
            <div className="flex items-center gap-2">
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: ANCHOR_COLORS[anchor.type] || '#fff' }}
              />
              <span className="font-medium">{anchor.name}</span>
              <span className="text-xs text-cad-muted ml-auto">{anchor.type}</span>
            </div>
            <div className="text-xs text-cad-muted ml-4 mt-0.5">
              ({anchor.position.map((v) => v.toFixed(1)).join(', ')})
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
