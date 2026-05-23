'use client';

import { useState, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';

const STLViewer = dynamic(() => import('../viewer/STLViewer'), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

const PART_TYPE_NAMES: Record<string, string> = {
  bracket: '支架',
  gear: '齿轮',
  motor_mount: '电机安装板',
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

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showCode, setShowCode] = useState(false);

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

    try {
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
      fetchHistory();
    } catch (err: any) {
      setError(err.message || '生成过程中出错');
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (text: string) => {
    setPrompt(text);
  };

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
              <p className="text-xs text-cad-muted">AI 参数化 CAD 生成平台</p>
            </div>
          </div>
          <div className="text-sm text-cad-muted">v1.0.0</div>
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
                placeholder="例如：生成一个带4个M6孔的L型支架"
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
                    生成中...
                  </span>
                ) : '生成 CAD 模型'}
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
                  '生成一个带4个M6孔的L型支架',
                  '创建一个模数2、20齿的齿轮',
                  '做一个NEMA17电机安装板',
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

          {/* Right: 3D Viewer & Code */}
          <div className="lg:col-span-2 space-y-4">
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
                {result?.stl_url ? (
                  <STLViewer url={`${API_BASE}${result.stl_url}`} />
                ) : (
                  <div className="h-full flex items-center justify-center text-cad-muted">
                    <div className="text-center">
                      <svg className="w-16 h-16 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      <p>输入描述并生成模型后可在此预览</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

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
          </div>
        </div>
      </div>
    </main>
  );
}
