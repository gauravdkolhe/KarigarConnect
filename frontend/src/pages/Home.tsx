import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  ArrowRight,
  Calculator,
  Compass,
  FileCheck2,
  Sparkles,
} from 'lucide-react';

interface HomeProps {
  onNavigate: (view: string) => void;
}

export const Home: React.FC<HomeProps> = ({ onNavigate }) => {
  const { user } = useAuth();

  return (
    <div>
      {/* Hero Section */}
      <section
        style={{
          padding: '4rem 1rem 3rem',
          textAlign: 'center',
          maxWidth: '900px',
          margin: '0 auto',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.85rem',
            background: 'var(--color-primary-light)',
            color: 'var(--color-primary)',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.85rem',
            fontWeight: 600,
            marginBottom: '1.5rem',
          }}
        >
          <Sparkles size={16} />
          <span>Empowering India's Heritage Crafts With Four Coordinated AI Agents</span>
        </div>

        <h1
          style={{
            fontSize: 'clamp(2.5rem, 5vw, 3.8rem)',
            fontWeight: 800,
            color: 'var(--color-text-main)',
            letterSpacing: '-0.02em',
            marginBottom: '1.25rem',
          }}
        >
          From Heritage Hands to{' '}
          <span style={{ color: 'var(--color-primary)' }}>Verified Global Buyers</span>
        </h1>

        <p
          style={{
            fontSize: '1.2rem',
            color: 'var(--color-text-muted)',
            lineHeight: 1.6,
            marginBottom: '2.5rem',
            maxWidth: '720px',
            margin: '0 auto 2.5rem',
          }}
        >
          KarigarConnect bridges traditional artisans with authentic wholesalers, retailers,
          and institutional buyers through AI image enhancement, bilingual cataloging, deterministic
          profit-guaranteed pricing, and transparent market linkage.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {user ? (
            <button
              className="btn btn-primary"
              style={{ padding: '0.85rem 1.75rem', fontSize: '1rem' }}
              onClick={() => {
                if (user.role === 'artisan') onNavigate('artisan-dashboard');
                else if (user.role === 'buyer') onNavigate('buyer-dashboard');
                else onNavigate('admin-dashboard');
              }}
            >
              <span>Go to Your {user.role.toUpperCase()} Dashboard</span>
              <ArrowRight size={18} />
            </button>
          ) : (
            <>
              <button
                className="btn btn-primary"
                style={{ padding: '0.85rem 1.75rem', fontSize: '1rem' }}
                onClick={() => onNavigate('register')}
              >
                <span>Join as an Artisan</span>
                <ArrowRight size={18} />
              </button>
              <button
                className="btn btn-outline"
                style={{ padding: '0.85rem 1.75rem', fontSize: '1rem' }}
                onClick={() => onNavigate('register')}
              >
                <span>Join as a Verified Buyer</span>
              </button>
            </>
          )}
        </div>
      </section>

      {/* Four Agents Architecture Overview */}
      <section style={{ margin: '4rem 0' }}>
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>The Four-Agent Intelligent Ecosystem</h2>
          <p style={{ color: 'var(--color-text-muted)' }}>
            Seamlessly integrated into a single cohesive product lifecycle.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '1.5rem',
          }}
        >
          {/* Agent 1 */}
          <div className="card">
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: '#FEF3C7',
                color: '#D97706',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
              }}
            >
              <Sparkles size={22} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>1. Image Processing Agent</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
              Automatically enhances raw workshop photos using Pillow algorithms, standardizing lighting,
              contrast, and color fidelity for commercial e-commerce presentation.
            </p>
          </div>

          {/* Agent 2 */}
          <div className="card">
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: '#ECFDF5',
                color: '#059669',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
              }}
            >
              <FileCheck2 size={22} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>2. Product Catalog Agent</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
              Generates compelling artisan storytelling, SEO keywords, and technical descriptions using Gemini,
              complete with a mandatory manual artisan approval gate.
            </p>
          </div>

          {/* Agent 3 */}
          <div className="card">
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: '#FDF3EE',
                color: '#C85A32',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
              }}
            >
              <Calculator size={22} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>3. Dynamic Pricing Agent</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
              Uses deterministic financial Decimal calculations to guarantee target margins over material,
              labor, packaging, overhead, marketplace commission, and shipping expenses.
            </p>
          </div>

          {/* Agent 4 */}
          <div className="card">
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: '#EFF6FF',
                color: '#2563EB',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
              }}
            >
              <Compass size={22} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>4. Market Linkage Agent</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
              Computes transparent compatibility scores against genuine buyer requirements in MongoDB, checking
              budgets, ready stock, monthly crafting capacity, and delivery lead times.
            </p>
          </div>
        </div>
      </section>

      {/* Role Switcher Call to Action */}
      <section
        style={{
          background: 'white',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '3rem 2rem',
          margin: '3rem 0',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <h2 style={{ fontSize: '1.85rem', marginBottom: '1rem' }}>Ready to Experience the Platform?</h2>
        <p style={{ color: 'var(--color-text-muted)', maxWidth: '600px', margin: '0 auto 2rem' }}>
          Test the live application across Artisan, Buyer, and Admin roles directly in your browser.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            className="btn btn-primary"
            onClick={() => onNavigate('login')}
          >
            <span>Login to KarigarConnect</span>
            <ArrowRight size={16} />
          </button>
          <button
            className="btn btn-outline"
            onClick={() => onNavigate('register')}
          >
            Create New Account
          </button>
        </div>
      </section>
    </div>
  );
};
