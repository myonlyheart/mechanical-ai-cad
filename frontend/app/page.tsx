'use client';

import { useState, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';
import VariantSelector from '../components/VariantSelector';
import AnalysisPanel from '../components/AnalysisPanel';
import AssemblyTree from '../components/AssemblyTree';
import { AnchorList } from '../components/AnchorVisualizer';
import ConstraintVisualizer from '../components/ConstraintVisualizer';
import ValidationUI from '../components/ValidationUI';
import BOMPanel from '../components/BOMPanel';

const STLViewer = dynamic(() => import('../viewer/STLViewer'), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

const PART_TYPE_NAMES: Record<string, string> = {
  bracket: '支架',
  gear: '齿轮',
  motor_mount: '电机安装板',
  bearing_block: '轴承座',
  flange: '法兰',
  coupling: '联轴器',
  shaft_sleeve: '轴套',
  bolt: '螺栓',
  nut: '螺母',
  washer: '垫片',
  shaft: '轴',
  bearing: '轴承',
  motor: '电机',
};

interface GenerationResult {
  id: number;
  stl_url: string;
  step_url: string;
  code: string;
  parameters: Record<string, any>;
  part_type: string;
  status: string;
}

interface HistoryItem {
  id: number;
  prompt: string;
  part_type: string;
  parameters: Record<string, any>;
  stl_url: string;
  created_at: string;
  status: string;
}

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

interface DesignResult {
  intent: {
    object: string;
    constraints: Record<string, any>;
    priority: string[];
  };
  variants: Variant[];
  comparison: ComparisonItem[];
  recommendation: string;
}

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showCode, setShowCode] = useState(false);

  // Multi-variant state
  const [designResult, setDesignResult] = useState<DesignResult | null>(null);
  const [selectedVariantId, setSelectedVariantId] = useState<string | null>(null);
  const [mode, setMode] = useState<'single' | 'multi' | 'assembly'>('multi');

  // Assembly state
  const [assemblyNodes, setAssemblyNodes] = useState<any[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [anchorHighlight, setAnchorHighlight] = useState<string | null>(null);

  // Validation state
  const [validationLoading, setValidationLoading] = useState(false);
  const [geoValidation, setGeoValidation] = useState<any>(null);
  const [mfgValidation, setMfgValidation] = useState<any>(null);
  const [collisionResult, setCollisionResult] = useState<any>(null);

  // Constraint state
  const [constraints, setConstraints] = useState<any[]>([]);
  const [solveResults, setSolveResults] = useState<any[]>([]);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/history?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.items || []);
      }
    } catch (err) {
      console.error('获取历史记录失败:', err);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    setDesignResult(null);
    setSelectedVariantId(null);

    try {
      if (mode === 'multi') {
        // Multi-variant pipeline: NL → designs
        const res = await fetch(`${API_BASE}/api/v1/generate-variants`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt }),
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || '生成失败');
        }

        const data = await res.json();
        setDesignResult(data);

        // Auto-select recommended variant
        if (data.recommendation) {
          setSelectedVariantId(data.recommendation);
        }
      } else {
        // Single-variant pipeline (legacy)
        const res = await fetch(`${API_BASE}/api/v1/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt }),
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || '生成失败');
        }

        const data = await res.json();
        setResult(data);
      }

      fetchHistory();
    } catch (err: any) {
      setError(err.message || '生成过程中出错');
    } finally {
      setLoading(false);
    }
  };

  const handleVariantSelect = async (variantId: string) => {
    setSelectedVariantId(variantId);
    if (!designResult) return;

    const variant = designResult.variants.find(v => v.design_id === variantId);
    if (!variant) return;

    // Generate STL for selected variant
    setGenLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: `${PART_TYPE_NAMES[designResult.intent.object] || designResult.intent.object} - ${variant.name}`,
          parameters: variant.params,
          part_type: designResult.intent.object,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.error('生成 STL 失败:', err);
    } finally {
      setGenLoading(false);
    }
  };

  const handleExampleClick = (text: string) => {
    setPrompt(text);
  };

  const handleRunValidation = async () => {
    if (!result?.parameters) return;
    setValidationLoading(true);
    try {
      const [geoRes, mfgRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/validate/geometry`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ parameters: result.parameters }),
        }),
        fetch(`${API_BASE}/api/v1/validate/manufacturing`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ parameters: result.parameters }),
        }),
      ]);
      if (geoRes.ok) setGeoValidation(await geoRes.json());
      if (mfgRes.ok) setMfgValidation(await mfgRes.json());
    } catch (err) {
      console.error('校验失败:', err);
    } finally {
      setValidationLoading(false);
    }
  };

  const selectedVariant = designResult?.variants.find(
    v => v.design_id === selectedVariantId
  );

  return (
    <main className="min-h-screen bg-cad-dark">
      {/* Header */}
      <header className="border-b border-cad-border bg-cad-panel">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cad-accent to-cad-accent2 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-cad-text">AI 机械 CAD 工作室</h1>
              <p className="text-xs text-cad-muted">生成式机械设计平台</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex bg-cad-dark rounded-lg p-0.5 border border-cad-border">
              <button
                onClick={() => setMode('multi')}
                className={`px-3 py-1 text-xs rounded-md transition-colors ${
                  mode === 'multi'
                    ? 'bg-cad-accent/20 text-cad-accent'
                    : 'text-cad-muted hover:text-cad-text'
                }`}
              >
                多方案模式
              </button>
              <button
                onClick={() => setMode('single')}
                className={`px-3 py-1 text-xs rounded-md transition-colors ${
                  mode === 'single'
                    ? 'bg-cad-accent/20 text-cad-accent'
                    : 'text-cad-muted hover:text-cad-text'
                }`}
              >
                单方案模式
              </button>
              <button
                onClick={() => setMode('assembly')}
                className={`px-3 py-1 text-xs rounded-md transition-colors ${
                  mode === 'assembly'
                    ? 'bg-cad-accent/20 text-cad-accent'
                    : 'text-cad-muted hover:text-cad-text'
                }`}
              >
                装配模式
              </button>
            </div>
            <div className="text-sm text-cad-muted">v1.1.0</div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Input */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-cad-panel border border-cad-border rounded-xl p-5">
              <h2 className="text-lg font-semibold mb-4 text-cad-text">描述您想要的零件</h2>

              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={mode === 'multi'
                  ? '例如：做一个轻量化电机支架，适配M4螺丝'
                  : mode === 'assembly'
                  ? '例如：将电机安装到底座上，使用螺栓固定'
                  : '例如：生成一个带4个M6孔的L型支架'}
                className="w-full h-32 bg-cad-dark border border-cad-border rounded-lg p-3 text-cad-text placeholder-cad-muted resize-none focus:outline-none focus:border-cad-accent transition-colors"
              />

              <button
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="w-full mt-3 py-3 bg-gradient-to-r from-cad-accent to-cyan-500 text-white font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    分析中...
                  </span>
                ) : mode === 'multi' ? '生成设计方案' : '生成 CAD 模型'}
              </button>

              {error && (
                <div className="mt-3 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
                  {error}
                </div>
              )}
            </div>

            {/* Example prompts */}
            <div className="bg-cad-panel border border-cad-border rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-3 text-cad-muted uppercase tracking-wider">示例</h3>
              <div className="space-y-2">
                {[
                  '做一个轻量化NEMA17电机支架，适配M4螺丝',
                  '创建一个20齿、模数2的标准直齿轮',
                  '做一个15度螺旋角的斜齿轮',
                  '设计一个模数2、长度100的齿条',
                  '设计一个608轴承座，基座安装',
                  '生成一个外径80的圆法兰，6个螺栓孔',
                  '做一个内径8的弹性联轴器',
                  '设计一个带凸缘和键槽的轴套',
                  '生成M6六角螺栓，长度20mm',
                  '做一个M8内六角螺钉',
                  '设计一个M6法兰螺母',
                  '设计一个直径8mm的键槽轴',
                  '生成一个台阶轴，12-8-6mm三段',
                  '生成6205深沟球轴承',
                  '做一个8mm轴径的法兰轴承',
                  '推荐一个NEMA17电机的安装座参数',
                  '设计一个NEMA23电机加强型安装座',
                  '做一个775电机紧凑安装支架',
                ].map((example, i) => (
                  <button
                    key={i}
                    onClick={() => handleExampleClick(example)}
                    className="w-full text-left p-2 text-sm text-cad-text/80 hover:text-cad-accent hover:bg-cad-dark rounded-lg transition-colors"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>

            {/* History */}
            {history.length > 0 && (
              <div className="bg-cad-panel border border-cad-border rounded-xl p-5">
                <h3 className="text-sm font-semibold mb-3 text-cad-muted uppercase tracking-wider">历史记录</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {history.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setPrompt(item.prompt)}
                      className="w-full text-left p-2 text-sm hover:bg-cad-dark rounded-lg transition-colors"
                    >
                      <div className="text-cad-text/80 truncate">{item.prompt}</div>
                      <div className="text-xs text-cad-muted mt-1">
                        {PART_TYPE_NAMES[item.part_type] || item.part_type}
                        {item.created_at && ` · ${new Date(item.created_at).toLocaleString('zh-CN')}`}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: Results */}
          <div className="lg:col-span-2 space-y-4">
            {/* Multi-variant: Variant Selector */}
            {designResult && mode === 'multi' && (
              <VariantSelector
                variants={designResult.variants}
                comparison={designResult.comparison}
                recommendation={designResult.recommendation}
                selectedId={selectedVariantId}
                onSelect={handleVariantSelect}
              />
            )}

            {/* 3D Viewer */}
            <div className="bg-cad-panel border border-cad-border rounded-xl overflow-hidden">
              <div className="p-4 border-b border-cad-border flex items-center justify-between">
                <h2 className="text-lg font-semibold text-cad-text">3D 预览</h2>
                {result && (
                  <div className="flex gap-2">
                    <a
                      href={`${API_BASE}${result.stl_url}`}
                      download
                      className="px-3 py-1 text-sm bg-cad-dark border border-cad-border rounded-lg text-cad-accent hover:bg-cad-accent/10 transition-colors"
                    >
                      下载 STL
                    </a>
                    <a
                      href={`${API_BASE}${result.step_url}`}
                      download
                      className="px-3 py-1 text-sm bg-cad-dark border border-cad-border rounded-lg text-cad-accent2 hover:bg-cad-accent2/10 transition-colors"
                    >
                      下载 STEP
                    </a>
                  </div>
                )}
              </div>
              <div className="h-[400px] viewer-grid">
                {genLoading ? (
                  <div className="h-full flex items-center justify-center text-cad-muted">
                    <div className="text-center">
                      <svg className="animate-spin w-8 h-8 mx-auto mb-3 text-cad-accent" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      <p>生成 3D 模型中...</p>
                    </div>
                  </div>
                ) : result?.stl_url ? (
                  <STLViewer url={`${API_BASE}${result.stl_url}`} />
                ) : (
                  <div className="h-full flex items-center justify-center text-cad-muted">
                    <div className="text-center">
                      <svg className="w-16 h-16 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      <p>{mode === 'multi' ? '选择设计方案后在此预览 3D 模型' : '输入描述并生成模型后可在此预览'}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Multi-variant: Analysis Panel */}
            {designResult && mode === 'multi' && (
              <AnalysisPanel
                constraintCheck={selectedVariant?.constraint_check || null}
                intent={designResult.intent}
              />
            )}

            {/* Assembly mode: Tree + Anchors + Constraints */}
            {mode === 'assembly' && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <AssemblyTree
                    nodes={assemblyNodes}
                    selectedId={selectedNodeId}
                    onSelect={setSelectedNodeId}
                    onToggleVisibility={(id) => {
                      setAssemblyNodes((prev) =>
                        prev.map((n) => (n.id === id ? { ...n, visible: !n.visible } : n))
                      );
                    }}
                    onToggleLock={(id) => {
                      setAssemblyNodes((prev) =>
                        prev.map((n) => (n.id === id ? { ...n, locked: !n.locked } : n))
                      );
                    }}
                  />
                  <AnchorList
                    anchors={[]}
                    selectedName={anchorHighlight}
                    onSelect={setAnchorHighlight}
                  />
                </div>
                <ConstraintVisualizer
                  constraints={constraints}
                  solveResults={solveResults}
                  onRemove={(id) => setConstraints((prev) => prev.filter((c) => c.id !== id))}
                />
              </div>
            )}

            {/* Generated code */}
            {result && (
              <div className="bg-cad-panel border border-cad-border rounded-xl overflow-hidden">
                <button
                  onClick={() => setShowCode(!showCode)}
                  className="w-full p-4 text-left flex items-center justify-between"
                >
                  <div>
                    <h2 className="text-lg font-semibold text-cad-text">生成的代码</h2>
                    <div className="flex gap-2 mt-1">
                      <span className="px-2 py-0.5 text-xs bg-cad-accent/20 text-cad-accent rounded">
                        {PART_TYPE_NAMES[result.part_type] || result.part_type}
                      </span>
                      <span className="px-2 py-0.5 text-xs bg-green-900/30 text-green-400 rounded">
                        {result.status}
                      </span>
                    </div>
                  </div>
                  <svg
                    className={`w-5 h-5 text-cad-muted transition-transform ${showCode ? 'rotate-180' : ''}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showCode && (
                  <div className="border-t border-cad-border">
                    <pre className="p-4 text-sm text-cad-text/90 overflow-x-auto bg-cad-dark/50">
                      <code>{result.code}</code>
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Parameters */}
            {result && (
              <div className="bg-cad-panel border border-cad-border rounded-xl p-4">
                <h3 className="text-sm font-semibold mb-2 text-cad-muted uppercase tracking-wider">参数</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(result.parameters).map(([key, value]) => (
                    <div key={key} className="bg-cad-dark rounded-lg p-2">
                      <div className="text-xs text-cad-muted">{key}</div>
                      <div className="text-sm text-cad-text font-mono">{String(value)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Validation UI */}
            {result && (
              <ValidationUI
                geometry={geoValidation}
                manufacturing={mfgValidation}
                collision={collisionResult}
                loading={validationLoading}
                onRunValidation={handleRunValidation}
              />
            )}

            {/* BOM Panel */}
            {result && (
              <BOMPanel
                resultParams={result.parameters}
                partType={result.part_type}
              />
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
