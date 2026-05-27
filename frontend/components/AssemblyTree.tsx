'use client';

import { useState } from 'react';

interface TreeNode {
  id: string;
  name: string;
  depth: number;
  has_part: boolean;
  visible: boolean;
  locked: boolean;
  world_position: [number, number, number];
  children?: TreeNode[];
}

interface AssemblyTreeProps {
  nodes: TreeNode[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  onToggleVisibility?: (id: string) => void;
  onToggleLock?: (id: string) => void;
}

export default function AssemblyTree({
  nodes,
  selectedId,
  onSelect,
  onToggleVisibility,
  onToggleLock,
}: AssemblyTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const renderNode = (node: TreeNode) => {
    const isSelected = selectedId === node.id;
    const hasChildren = (node.children?.length ?? 0) > 0;
    const isExpanded = expandedIds.has(node.id);

    return (
      <div key={node.id}>
        <div
          className={`flex items-center gap-1 px-2 py-1.5 rounded-md cursor-pointer transition-colors text-sm ${
            isSelected
              ? 'bg-cad-accent/20 text-cad-accent'
              : 'hover:bg-cad-dark text-cad-text/80'
          }`}
          style={{ paddingLeft: `${node.depth * 16 + 8}px` }}
          onClick={() => onSelect?.(node.id)}
        >
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpand(node.id);
              }}
              className="w-4 h-4 flex items-center justify-center text-cad-muted"
            >
              {isExpanded ? '▾' : '▸'}
            </button>
          ) : (
            <span className="w-4" />
          )}

          <span className={`flex-1 truncate ${node.has_part ? 'font-medium' : 'text-cad-muted'}`}>
            {node.has_part ? '◆ ' : '📁 '}
            {node.name}
          </span>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleVisibility?.(node.id);
            }}
            className={`w-5 h-5 text-xs ${node.visible ? 'text-cad-muted' : 'text-red-400'}`}
            title={node.visible ? '隐藏' : '显示'}
          >
            {node.visible ? '👁' : '🚫'}
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleLock?.(node.id);
            }}
            className={`w-5 h-5 text-xs ${node.locked ? 'text-yellow-400' : 'text-cad-muted'}`}
            title={node.locked ? '解锁' : '锁定'}
          >
            {node.locked ? '🔒' : '🔓'}
          </button>
        </div>

        {hasChildren && isExpanded && node.children?.map(renderNode)}
      </div>
    );
  };

  if (nodes.length === 0) {
    return (
      <div className="p-4 text-center text-cad-muted text-sm">
        暂无装配数据
      </div>
    );
  }

  return (
    <div className="bg-cad-panel border border-cad-border rounded-xl overflow-hidden">
      <div className="p-3 border-b border-cad-border">
        <h3 className="text-sm font-semibold text-cad-text">装配树</h3>
      </div>
      <div className="p-2 space-y-0.5 max-h-80 overflow-y-auto">
        {nodes.map(renderNode)}
      </div>
    </div>
  );
}
