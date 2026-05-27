'use client';

import { useState } from 'react';

interface BOMItem {
  part_number: string;
  part_name: string;
  material: string;
  quantity: number;
  weight_g: number;
  manufacturing_method: string;
  notes: string;
}

interface BOMData {
  title: string;
  total_parts: number;
  unique_parts: number;
  total_weight_g: number;
  items: BOMItem[];
}

interface BOMPanelProps {
  resultParams?: Record<string, any>;
  partType?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function BOMPanel({ resultParams, partType }: BOMPanelProps) {
  const [bom, setBom] = useState<BOMData | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);

  const handleGenerate = async () => {
    if (!resultParams) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/bom/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parts: [
            {
              name: resultParams.name || partType || 'part',
              part_type: partType || 'bracket',
              parameters: resultParams,
              metadata: {},
            },
          ],
          title: `${partType || 'Part'} BOM`,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setBom(data);
      }
    } catch (err) {
      console.error('BOM 生成失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCSV = async () => {
    if (!resultParams) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/bom/export/csv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parts: [
            {
              name: resultParams.name || partType || 'part',
              part_type: partType || 'bracket',
              parameters: resultParams,
              metadata: {},
            },
          ],
        }),
      });
      if (res.ok) {
        const data = await res.json();
        const blob = new Blob([data.csv], { type: 'text/csv;charset=utf-8-sig;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bom_${partType || 'part'}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('CSV 导出失败:', err);
    }
  };

  return (
    <div className="bg-cad-panel border border-cad-border rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-cad-dark/30 transition-colors"
      >
        <h2 className="text-lg font-semibold text-cad-text">BOM 物料清单</h2>
        <div className="flex items-center gap-2">
          {!bom && resultParams && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                handleGenerate();
              }}
              className="px-3 py-1 text-xs bg-cad-accent/20 text-cad-accent rounded-lg hover:bg-cad-accent/30 transition-colors cursor-pointer"
            >
              {loading ? '生成中...' : '生成 BOM'}
            </span>
          )}
          {bom && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                handleDownloadCSV();
              }}
              className="px-3 py-1 text-xs bg-green-900/30 text-green-400 rounded-lg hover:bg-green-900/50 transition-colors cursor-pointer"
            >
              下载 CSV
            </span>
          )}
          <svg
            className={`w-5 h-5 text-cad-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-cad-border">
          {!bom && !resultParams && (
            <p className="p-4 text-sm text-cad-muted text-center">
              生成零件后可查看物料清单
            </p>
          )}

          {!bom && resultParams && (
            <p className="p-4 text-sm text-cad-muted text-center">
              点击 &quot;生成 BOM&quot; 查看物料清单
            </p>
          )}

          {bom && (
            <>
              {/* Summary */}
              <div className="p-3 bg-cad-dark/50 flex items-center gap-6 text-sm">
                <div>
                  <span className="text-cad-muted">总件数: </span>
                  <span className="text-cad-text font-mono">{bom.total_parts}</span>
                </div>
                <div>
                  <span className="text-cad-muted">种类: </span>
                  <span className="text-cad-text font-mono">{bom.unique_parts}</span>
                </div>
                <div>
                  <span className="text-cad-muted">总重量: </span>
                  <span className="text-cad-text font-mono">{bom.total_weight_g.toFixed(1)}g</span>
                </div>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-cad-border text-cad-muted">
                      <th className="px-3 py-2 text-left font-medium">零件编号</th>
                      <th className="px-3 py-2 text-left font-medium">名称</th>
                      <th className="px-3 py-2 text-left font-medium">材料</th>
                      <th className="px-3 py-2 text-right font-medium">数量</th>
                      <th className="px-3 py-2 text-right font-medium">重量(g)</th>
                      <th className="px-3 py-2 text-left font-medium">制造方式</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bom.items.map((item, i) => (
                      <tr
                        key={i}
                        className="border-b border-cad-border/50 hover:bg-cad-dark/30 transition-colors"
                      >
                        <td className="px-3 py-2 font-mono text-cad-accent">
                          {item.part_number}
                        </td>
                        <td className="px-3 py-2 text-cad-text">{item.part_name}</td>
                        <td className="px-3 py-2 text-cad-text/80">{item.material}</td>
                        <td className="px-3 py-2 text-right font-mono text-cad-text">
                          {item.quantity}
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-cad-text">
                          {item.weight_g.toFixed(1)}
                        </td>
                        <td className="px-3 py-2 text-cad-text/80">
                          {item.manufacturing_method || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
