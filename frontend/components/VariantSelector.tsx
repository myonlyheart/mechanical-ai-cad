'use client';

interface Variant {
  design_id: string;
  name: string;
  description: string;
  params: Record<string, any>;
  performance: {
    weight: string;
    strength: string;
    print_time: string;
  };
  constraint_check: {
    valid: boolean;
    fixes_applied: string[];
    remaining_issues: any[];
  };
}

interface ComparisonItem {
  design_id: string;
  name: string;
  weight_g: number;
  print_time_hours: number;
  material_cost_yuan: number;
  total_cost_yuan: number;
}

interface VariantSelectorProps {
  variants: Variant[];
  comparison: ComparisonItem[];
  recommendation: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const WEIGHT_COLORS: Record<string, string> = {
  '极轻': 'text-green-400',
  '轻': 'text-green-400',
  '中等': 'text-yellow-400',
  '重': 'text-red-400',
};

const STRENGTH_COLORS: Record<string, string> = {
  '极高': 'text-green-400',
  '高': 'text-green-400',
  '中等': 'text-yellow-400',
  '低': 'text-red-400',
};

export default function VariantSelector({
  variants,
  comparison,
  recommendation,
  selectedId,
  onSelect,
}: VariantSelectorProps) {
  if (!variants.length) return null;

  return (
    <div className="bg-cad-panel border border-cad-border rounded-xl p-5">
      <h2 className="text-lg font-semibold text-cad-text mb-4">
        设计方案对比
        <span className="ml-2 text-xs text-cad-muted font-normal">
          {variants.length} 种方案
        </span>
      </h2>

      {/* 方案卡片 */}
      <div className="space-y-3">
        {variants.map((variant) => {
          const isSelected = selectedId === variant.design_id;
          const isRecommended = variant.design_id === recommendation;
          const comp = comparison.find(c => c.design_id === variant.design_id);

          return (
            <button
              key={variant.design_id}
              onClick={() => onSelect(variant.design_id)}
              className={`w-full text-left p-4 rounded-lg border transition-all ${
                isSelected
                  ? 'border-cad-accent bg-cad-accent/10'
                  : 'border-cad-border hover:border-cad-accent/50 bg-cad-dark/50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-cad-text font-semibold">{variant.name}</span>
                  {isRecommended && (
                    <span className="px-2 py-0.5 text-xs bg-green-900/40 text-green-400 rounded-full">
                      推荐
                    </span>
                  )}
                  {!variant.constraint_check.valid && (
                    <span className="px-2 py-0.5 text-xs bg-yellow-900/40 text-yellow-400 rounded-full">
                      需修复
                    </span>
                  )}
                </div>
                {isSelected && (
                  <svg className="w-5 h-5 text-cad-accent" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                )}
              </div>

              <p className="text-sm text-cad-muted mb-3">{variant.description}</p>

              {/* 性能指标 */}
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="bg-cad-dark rounded p-2 text-center">
                  <div className="text-xs text-cad-muted">重量</div>
                  <div className={WEIGHT_COLORS[variant.performance.weight] || 'text-cad-text'}>
                    {variant.performance.weight}
                  </div>
                </div>
                <div className="bg-cad-dark rounded p-2 text-center">
                  <div className="text-xs text-cad-muted">强度</div>
                  <div className={STRENGTH_COLORS[variant.performance.strength] || 'text-cad-text'}>
                    {variant.performance.strength}
                  </div>
                </div>
                <div className="bg-cad-dark rounded p-2 text-center">
                  <div className="text-xs text-cad-muted">打印时间</div>
                  <div className="text-cad-text">{variant.performance.print_time}</div>
                </div>
              </div>

              {/* 约束检查状态 */}
              {variant.constraint_check.fixes_applied.length > 0 && (
                <div className="mt-2 text-xs text-yellow-400">
                  自动修复: {variant.constraint_check.fixes_applied.join('; ')}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* 成本对比表 */}
      {comparison.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-cad-muted mb-2">成本估算</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-cad-muted text-xs border-b border-cad-border">
                  <th className="text-left py-2 px-2">方案</th>
                  <th className="text-right py-2 px-2">重量</th>
                  <th className="text-right py-2 px-2">打印时间</th>
                  <th className="text-right py-2 px-2">材料费</th>
                  <th className="text-right py-2 px-2">总费用</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((item) => (
                  <tr
                    key={item.design_id}
                    className={`border-b border-cad-border/50 ${
                      item.design_id === recommendation ? 'text-green-400' : 'text-cad-text'
                    }`}
                  >
                    <td className="py-2 px-2">{item.name}</td>
                    <td className="text-right py-2 px-2">{item.weight_g}g</td>
                    <td className="text-right py-2 px-2">{item.print_time_hours}h</td>
                    <td className="text-right py-2 px-2">¥{item.material_cost_yuan}</td>
                    <td className="text-right py-2 px-2 font-mono">¥{item.total_cost_yuan}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
