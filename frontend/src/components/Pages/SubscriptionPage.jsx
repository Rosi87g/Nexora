import React, { useState } from 'react';
import './SubscriptionPage.css';

const SubscriptionPage = () => {
  const [activePlan, setActivePlan] = useState('go');

  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: '₹0',
      priceDetail: '₹0 INR/month',
      description: 'Basic AI features',
      isPopular: false,
      features: [
        'Simple explanations',
        'Short chats for common questions',
        'Limited image generation',
        'Basic memory and context',
        'Help with planning and tasks',
        'Explore basic features'
      ],
      ctaText: 'Current Plan',
      ctaClass: 'current-plan'
    },
    {
      id: 'go',
      name: 'Go',
      price: '₹399',
      priceDetail: '₹399 INR/month',
      description: 'Enhanced AI capabilities',
      isPopular: true,
      features: [
        'Deeper analysis for tough questions',
        'Longer chats & more content uploads',
        'High-quality image generation',
        'Advanced memory for smarter replies',
        'Enhanced planning and task management',
        'Priority support'
      ],
      ctaText: 'Upgrade to Go',
      ctaClass: 'upgrade-primary'
    },
    {
      id: 'advanced',
      name: 'Advanced',
      price: '₹4,990',
      priceDetail: '₹4,990 INR/year (save 17%)',
      description: 'Ultimate AI experience',
      isPopular: false,
      features: [
        'Solve complex problems instantly',
        'Unlimited chat sessions',
        'Unlimited image generation',
        'Full conversation memory',
        'AI agent mode for planning',
        'Advanced project organization',
        'Priority customer support'
      ],
      ctaText: 'Get Advanced',
      ctaClass: 'get-plan'
    }
  ];

  const handleUpgrade = (planId) => {
    if (planId === 'free') return;

    console.log(`🎉 Upgrading to ${planId} plan!`);
    alert(`Successfully upgraded to ${planId.toUpperCase()} plan!\n\nRedirecting back to Nexora...`);
    window.history.back();
  };

  const handleBack = () => {
    window.history.back();
  };

  return (
    <div className="subscription-page">

      {/* ✅ MAIN CONTENT - FULL SCROLLABLE */}
      <main className="subscription-main">
        {/* PROMO BANNER */}
        <section className="promo-banner">
          <div className="banner-content">
            <h2 className="banner-title">
              <span className="highlight">Try Go </span> for 12 months
            </h2>
            <p className="banner-subtitle">
              Upgrade today and unlock powerful AI features for just ₹399/month
            </p>
          </div>
        </section>

        {/* PLAN TOGGLE */}
        <section className="plan-toggle-section">
          <div className="plan-toggle">
            <button
              className={`toggle-btn ${activePlan === 'free' ? 'active' : ''}`}
              onClick={() => setActivePlan('free')}
            >
              Free
            </button>
            <button
              className={`toggle-btn ${activePlan === 'go' ? 'active' : ''}`}
              onClick={() => setActivePlan('go')}
            >
              Go
            </button>
            <button
              className={`toggle-btn ${activePlan === 'advanced' ? 'active' : ''}`}
              onClick={() => setActivePlan('advanced')}
            >
              Advanced
            </button>
          </div>
        </section>

        {/* PLANS GRID */}
        <section className="plans-section">
          <div className="plans-grid">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`plan-card 
                  ${plan.isPopular ? 'popular' : ''} 
                  ${activePlan === plan.id ? 'active' : ''}`}
              >
                {plan.isPopular && <div className="popular-badge">MOST POPULAR</div>}

                <div className="plan-header">
                  <h3 className="plan-name">{plan.name}</h3>
                  <div className="plan-price-container">
                    <div className="plan-price">{plan.price}</div>
                    <div className="plan-price-detail">{plan.priceDetail}</div>
                  </div>
                  <p className="plan-description">{plan.description}</p>
                </div>

                <button
                  className={`plan-cta ${plan.ctaClass}`}
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={plan.id === 'free'}
                >
                  {plan.ctaText}
                </button>

                <ul className="features-list">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="feature-item">
                      <span className="feature-icon">✓</span>
                      <span className="feature-text">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* ✅ FOOTER */}
      <footer className="subscription-footer">
        <div className="footer-content">
          <button
            className="footer-back-btn"
            onClick={() => window.location.href = '/'} // ✅ 1-LINE SOLUTION
          >
            ← Back to Nexora
          </button>
          <div className="footer-links">
            <a href="#" className="footer-link">Terms</a>
            <a href="#" className="footer-link">Privacy</a>
            <a href="#" className="footer-link">Help</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default SubscriptionPage;