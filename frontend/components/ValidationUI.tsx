'use client';

import { useState } from 'react';

interface ValidationIssue {
  code: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  fix_suggestion?: string;
  process?: string;
  field?: string;
}

interface GeometryValidation {
  valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  checks_performed: string[];
}

interface ManufacturingValidation {
  valid: boolean;
  issues: ValidationIssue[];
  processes_checked: string[];
}

interface CollisionResult {
  has_collision: boolean;
  collisions: Array<{
    part_a: string;
    part_b: string;
    overlap_volume: number;
  }>;
}

interface ValidationUIProps {
  geometry?: GeometryValidation | null;
  manufacturing?: ManufacturingValidation | null;
  collision?: CollisionResult | null;
  loading?: boolean;
  onRunValidation?: () => void;
}

const PROCESS_LABELS: Record<string, string> = {
  fdm_3d_print: 'FDM 3D打印',
  cnc_milling: 'CNC铣削',
  injection_molding: '注塑',
};

function IssueCard({ issue }: { issue: ValidationIssue }) {
  const isError = issue.severity === 'error';
  const isWarning = issue.severity === 'warning';

  return (
    <div
      className={`p-3 rounded-lg border ${
        isError
          ? 'bg-red-900/20 border-red-800/50'
          : isWarning
          ? 'bg-yellow-900/20 border-yellow-800/50'
          : 'bg-blue-900/20 border-blue-800/50'
      }`}
    >
      <div className="flex items-start gap-2">
        <span
          className={`font-bold text-sm mt-0.5 ${
            isError ? 'text-red-400' : isWarning ? 'text-yellow-400' : 'text-blue-400'
          }`}
        >
          {isError ? '!' : isWarning ? '⚠' : 'i'}
        </span>
        <div className="flex-1 min-w-0">
          <p
            className={`text-sm font-medium ${
              isError ? 'text-red-400' : isWarning ? 'text-yellow-400' : 'text-blue-400'
            }`}
          >
            {issue.message}
          </p>
          {issue.fix_suggestion && (
            <p className="text-xs text-green-400/80 mt-1">
              建议: {issue.fix_suggestion}
            </p>
          )}
          <div className="flex items-center gap-2 mt-1">
            <code className="text-[10px] text-cad-muted">{issue.code}</code>
            {issue.process && (
              <span className="text-[10px] text-cad-muted">
                {PROCESS_LABELS[issue.process] || issue.process}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function SectionHeader({
  title,
  valid,
  count,
}: {
  title: string;
  valid: boolean;
  count: number;
}) {
  return (
    <div className="flex items-center gap-2">
      {valid ? (
        <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      ) : (
        <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      )}
      <span className="text-sm font-semibold text-cad-text">{title}</span>
      {!valid && (
        <span className="text-xs text-red-400">({count} 个问题)</span>
      )}
    </div>
  );
}

export default function ValidationUI({
  geometry,
  manufacturing,
  collision,
  loading = false,
  onRunValidation,
}: ValidationUIProps) {
  const [expanded, setExpanded] = useState(true);

  const hasResults = geometry || manufacturing || collision;
  const allValid =
    (geometry?.valid ?? true) &&
    (manufacturing?.valid ?? true) &&
    !(collision?.has_collision ?? false);

  const totalIssues =
    (geometry?.errors.length || 0) +
    (geometry?.warnings.length || 0) +
    (manufacturing?.issues.length || 0) +
    (collision?.collisions.length || 0);

  return (
    <div className="bg-cad-panel border border-cad-border rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-cad-dark/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-cad-text">校验结果</h2>
          {hasResults && (
            <span
              className={`px-2 py-0.5 text-xs rounded ${
                allValid
                  ? 'bg-green-900/30 text-green-400'
                  : 'bg-red-900/30 text-red-400'
              }`}
            >
              {allValid ? '全部通过' : `${totalIssues} 个问题`}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onRunValidation && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                onRunValidation();
              }}
              className="px-3 py-1 text-xs bg-cad-accent/20 text-cad-accent rounded-lg hover:bg-cad-accent/30 transition-colors cursor-pointer"
            >
              {loading ? '校验中...' : '运行校验'}
            </span>
          )}
          <svg
            className={`w-5 h-5 text-cad-muted transition-transform ${
              expanded ? 'rotate-180' : ''
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-cad-border p-4 space-y-4">
          {!hasResults && !loading && (
            <p className="text-sm text-cad-muted text-center py-4">
              点击 &quot;运行校验&quot; 检查几何、制造和碰撞问题
            </p>
          )}

          {loading && (
            <div className="flex items-center justify-center py-6">
              <svg
                className="animate-spin w-6 h-6 text-cad-accent"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              <span className="ml-2 text-sm text-cad-muted">校验中...</span>
            </div>
          )}

          {/* Geometry validation */}
          {geometry && (
            <div className="space-y-2">
              <SectionHeader
                title="几何校验"
                valid={geometry.valid}
                count={geometry.errors.length + geometry.warnings.length}
              />
              {geometry.errors.map((issue, i) => (
                <IssueCard key={`geo-e-${i}`} issue={issue} />
              ))}
              {geometry.warnings.map((issue, i) => (
                <IssueCard key={`geo-w-${i}`} issue={issue} />
              ))}
              {geometry.valid && (
                <p className="text-xs text-green-400/70 ml-6">
                  检查项: {geometry.checks_performed.join(', ')}
                </p>
              )}
            </div>
          )}

          {/* Manufacturing validation */}
          {manufacturing && (
            <div className="space-y-2">
              <SectionHeader
                title="制造校验"
                valid={manufacturing.valid}
                count={manufacturing.issues.length}
              />
              {manufacturing.issues.map((issue, i) => (
                <IssueCard key={`mfg-${i}`} issue={issue} />
              ))}
              {manufacturing.valid && (
                <p className="text-xs text-green-400/70 ml-6">
                  工艺: {manufacturing.processes_checked.map((p) => PROCESS_LABELS[p] || p).join(', ')}
                </p>
              )}
            </div>
          )}

          {/* Collision detection */}
          {collision && (
            <div className="space-y-2">
              <SectionHeader
                title="碰撞检测"
                valid={!collision.has_collision}
                count={collision.collisions.length}
              />
              {collision.collisions.map((col, i) => (
                <div
                  key={`col-${i}`}
                  className="p-3 rounded-lg border bg-red-900/20 border-red-800/50"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-red-400 font-bold text-sm">!</span>
                    <div>
                      <p className="text-sm text-red-400 font-medium">
                        {col.part_a} 与 {col.part_b} 发生碰撞
                      </p>
                      <p className="text-xs text-cad-muted mt-1">
                        重叠体积: {col.overlap_volume.toFixed(2)} mm³
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              {!collision.has_collision && (
                <p className="text-xs text-green-400/70 ml-6">无碰撞检测</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
