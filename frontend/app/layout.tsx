import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI 机械 CAD 工作室',
  description: 'AI 参数化 CAD 生成平台',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-cad-dark">{children}</body>
    </html>
  );
}
