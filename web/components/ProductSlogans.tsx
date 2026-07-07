export interface Slogan {
  icon: string;
  title: string;
  description: string;
}

export const SLOGANS: Slogan[] = [
  {
    icon: "🔄",
    title: "团队间以 brief 转移为工作天然分界",
    description: "团队内支持传统看板模式，跨团队协作以 brief 为清晰边界。",
  },
  {
    icon: "🤖",
    title: "平等对待上下游",
    description: "以 AI 审核优化需求质量，让上下游信息对等、协作更顺畅。",
  },
  {
    icon: "🔁",
    title: "全链路透明闭环",
    description: "自动聚合下游进展，从需求发起到完成，状态一目了然。",
  },
];

export default function ProductSlogans() {
  return (
    <div className="slogans">
      <h3 className="slogans-title">产品特点</h3>
      <div className="slogan-list">
        {SLOGANS.map((slogan) => (
          <div key={slogan.title} className="slogan-card">
            <div className="slogan-icon" aria-hidden="true">
              {slogan.icon}
            </div>
            <div className="slogan-content">
              <h4 className="slogan-title">{slogan.title}</h4>
              <p className="slogan-description">{slogan.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
