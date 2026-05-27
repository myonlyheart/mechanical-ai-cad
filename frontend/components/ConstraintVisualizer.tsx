'use client';

interface MateConstraint {
  id: string;
  type: string;
  source_part: string;
  source_anchor: string;
  target_part: string;
  target_anchor: string;
  value: number;
  solved: boolean;
}

interface SolveResult {
  mate_id: string;
  valid: boolean;
  message: string;
  translation?: [number, number, number];
}

interface ConstraintVisualizerProps {
  constraints: MateConstraint[];
  solveResults?: SolveResult[];
  onRemove?: (id: string) => void;
}

const TYPE_LABELS: Record<string, string> = {
  coincident: '重合',
  concentric: '同心',
  parallel: '平行',
  tangent: '相切',
  distance: '距离',
  angle: '角度',
};

const TYPE_COLORS: Record<string, string> = {
  coincident: '#ff6b6b',
  concentric: '#4ecdc4',
  parallel: '#ffd93d',
  tangent: '#6bcb77',
  distance: '#9b59b6',
  angle: '#e67e22',
};

export default function ConstraintVisualizer({
  constraints,
  solveResults = [],
  onRemove,
}: ConstraintVisualizerProps) {
  if (constraints.length === 0) {
    return (
      <div className="bg-cad-panel border border-cad-border rounded-xl p-4">
        <h3 className="text-sm font-semibold text-cad-muted uppercase tracking-wider mb-2">
          装配约束
        </h3>
        <p className="text-sm text-cad-muted">暂无约束</p>
      </div>
    );
  }

  const getResultForMate = (mateId: string) =>
    solveResults.find((r) => r.mate_id === mateId);

  const solvedCount = solveResults.filter((r) => r.valid).length;
  const totalCount = constraints.length;

  return (
    <div className="bg-cad-panel border border-cad-border rounded-xl overflow-hidden">
      <div className="p-3 border-b border-cad-border flex items-center justify-between">
        <h3 className="text-sm font-semibold text-cad-text">装配约束</h3>
        <span className="text-xs text-cad-muted">
          {solveResults.length > 0
            ? `${solvedCount}/${totalCount} 已求解`
            : `${totalCount} 个约束`}
        </span>
      </div>
      <div className="divide-y divide-cad-border">
        {constraints.map((mate) => {
          const result = getResultForMate(mate.id);
          const color = TYPE_COLORS[mate.type] || '#888';

          return (
            <div key={mate.id} className="p-3 hover:bg-cad-dark/50 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-sm font-medium text-cad-text">
                      {TYPE_LABELS[mate.type] || mate.type}
                    </span>
                    {mate.value > 0 && (
                      <span className="text-xs text-cad-muted font-mono">
                        {mate.value}mm
                      </span>
                    )}
                    {result && (
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          result.valid
                            ? 'bg-green-900/30 text-green-400'
                            : 'bg-red-900/30 text-red-400'
                        }`}
                      >
                        {result.valid ? '已满足' : '未满足'}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-cad-muted mt-1 ml-4">
                    <span className="text-cad-accent">{mate.source_part}</span>
                    <span className="mx-1">.</span>
                    <span>{mate.source_anchor}</span>
                    <span className="mx-2">→</span>
                    <span className="text-cad-accent2">{mate.target_part}</span>
                    <span className="mx-1">.</span>
                    <span>{mate.target_anchor}</span>
                  </div>
                  {result?.message && (
                    <div className="text-xs text-cad-muted/80 mt-1 ml-4">
                      {result.message}
                    </div>
                  )}
                </div>
                {onRemove && (
                  <button
                    onClick={() => onRemove(mate.id)}
                    className="text-cad-muted hover:text-red-400 transition-colors p-1"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
