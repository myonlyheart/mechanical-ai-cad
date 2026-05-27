'use client';

interface ConstraintIssue {
  code: string;
  field: string;
  message: string;
  severity: 'error' | 'warning';
  fixable: boolean;
}

interface ConstraintCheck {
  valid: boolean;
  issues?: ConstraintIssue[];
  fixes_applied: string[];
  remaining_issues: any[];
}

interface AnalysisPanelProps {
  constraintCheck: ConstraintCheck | null;
  intent: {
    object: string;
    constraints: Record<string, any>;
    priority: string[];
  } | null;
}

const SEVERITY_STYLES: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  error: {
    bg: 'bg-red-900/20',
    border: 'border-red-800/50',
    text: 'text-red-400',
    icon: '!',
  },
  warning: {
    bg: 'bg-yellow-900/20',
    border: 'border-yellow-800/50',
    text: 'text-yellow-400',
    icon: '⚠',
  },
};

const PRIORITY_LABELS: Record<string, string> = {
  lightweight: '轻量化',
  rigid: '高刚性',
  printable: '易打印',
  fast_print: '快速打印',
  low_cost: '低成本',
};

export default function AnalysisPanel({ constraintCheck, intent }: AnalysisPanelProps) {
  if (!constraintCheck && !intent) return null;

  const issues: ConstraintIssue[] = constraintCheck?.issues || [];
  const fixesApplied = constraintCheck?.fixes_applied || [];
  const remainingIssues: any[] = constraintCheck?.remaining_issues || [];
  const isValid = constraintCheck?.valid ?? true;

  return (
    <div className="bg-cad-panel border border-cad-border rounded-xl p-5 space-y-4">
      <h2 className="text-lg font-semibold text-cad-text">设计分析</h2>

      {/* 设计意图摘要 */}
      {intent && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-cad-muted">设计意图</h3>
          <div className="flex flex-wrap gap-2">
            <span className="px-2 py-1 text-xs bg-cad-accent/20 text-cad-accent rounded">
              {intent.object === 'motor_mount' ? '电机安装板'
                : intent.object === 'bracket' ? '支架'
                : intent.object === 'gear' ? '齿轮'
                : intent.object}
            </span>
            {Object.entries(intent.constraints).map(([key, value]) => (
              <span key={key} className="px-2 py-1 text-xs bg-cad-dark text-cad-text/80 rounded border border-cad-border">
                {key}: {String(value)}
              </span>
            ))}
          </div>
          {intent.priority.length > 0 && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-cad-muted">优先级:</span>
              {intent.priority.map((p, i) => (
                <span key={p} className="flex items-center gap-1 text-xs">
                  <span className="w-4 h-4 flex items-center justify-center rounded-full bg-cad-accent/20 text-cad-accent text-[10px] font-bold">
                    {i + 1}
                  </span>
                  <span className="text-cad-text/80">{PRIORITY_LABELS[p] || p}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 约束检查总览 */}
      {constraintCheck && (
        <div className={`p-3 rounded-lg border ${
          isValid
            ? 'bg-green-900/20 border-green-800/50'
            : 'bg-red-900/20 border-red-800/50'
        }`}>
          <div className="flex items-center gap-2">
            {isValid ? (
              <>
                <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-sm text-green-400 font-medium">所有约束检查通过</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="text-sm text-red-400 font-medium">
                  发现 {issues.length} 个问题
                </span>
              </>
            )}
          </div>
        </div>
      )}

      {/* 问题列表 */}
      {issues.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-cad-muted">
            检查详情
            <span className="ml-1 font-normal text-cad-muted">({issues.length})</span>
          </h3>
          <div className="space-y-2">
            {issues.map((issue, idx) => {
              const style = SEVERITY_STYLES[issue.severity] || SEVERITY_STYLES.warning;
              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border ${style.bg} ${style.border}`}
                >
                  <div className="flex items-start gap-2">
                    <span className={`${style.text} font-bold text-sm mt-0.5`}>{style.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`${style.text} text-sm font-medium`}>{issue.message}</span>
                        {issue.fixable && (
                          <span className="px-1.5 py-0.5 text-[10px] bg-green-900/30 text-green-400 rounded">
                            可自动修复
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-cad-muted mt-1">
                        字段: <code className="text-cad-text/70">{issue.field}</code>
                        {' · '}
                        代码: <code className="text-cad-text/70">{issue.code}</code>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 自动修复记录 */}
      {fixesApplied.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-cad-muted">
            已自动修复
            <span className="ml-1 font-normal text-cad-muted">({fixesApplied.length})</span>
          </h3>
          <div className="space-y-1">
            {fixesApplied.map((fix, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 p-2 rounded bg-green-900/10 border border-green-800/30 text-sm"
              >
                <svg className="w-4 h-4 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="text-green-400/90">{fix}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 剩余未修复问题 */}
      {remainingIssues.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-red-400">
            需手动处理
            <span className="ml-1 font-normal">({remainingIssues.length})</span>
          </h3>
          <div className="space-y-1">
            {remainingIssues.map((issue: any, idx: number) => (
              <div
                key={idx}
                className="flex items-center gap-2 p-2 rounded bg-red-900/10 border border-red-800/30 text-sm"
              >
                <span className="text-red-400 font-bold">!</span>
                <span className="text-red-400/90">{issue.message || String(issue)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
