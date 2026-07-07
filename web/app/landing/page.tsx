import Link from "next/link";
import ProductSlogans from "@/components/ProductSlogans";

export default function LandingPage() {
  return (
    <div className="landing-page">
      <header className="landing-header">
        <Link href="/landing" className="landing-brand">
          <span className="landing-brand-name">BriefChain</span>
        </Link>
        <div className="landing-actions">
          <Link href="/login" className="btn">登录</Link>
          <Link href="/register" className="btn btn-primary">注册</Link>
        </div>
      </header>

      <main className="landing-main">
        <div className="landing-hero">
          <h1 className="landing-title">AI-reviewed briefs for smoother handoffs</h1>
          <p className="landing-subtitle">
            让团队间的需求交接更清晰、更可控
          </p>
          <Link href="/briefs" className="btn btn-primary landing-cta">
            进入应用
          </Link>
        </div>

        <ProductSlogans />
      </main>
    </div>
  );
}
