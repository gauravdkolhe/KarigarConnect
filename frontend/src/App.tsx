import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { ArtisanDashboard } from './pages/ArtisanDashboard';
import { ProductWorkflowWizard } from './pages/ProductWorkflowWizard';
import { BuyerDashboard } from './pages/BuyerDashboard';
import { InquiriesPage } from './pages/InquiriesPage';
import { AdminDashboard } from './pages/AdminDashboard';
import { ProfilePage } from './pages/ProfilePage';
import './index.css';

const MainApp: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [currentView, setCurrentView] = useState<string>('home');
  const [viewData, setViewData] = useState<any>(null);

  // Navigation handler
  const handleNavigate = (view: string, data?: any) => {
    setCurrentView(view);
    if (data !== undefined) {
      setViewData(data);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Determine view rendering
  const renderView = () => {
    // Public routes or fallback
    if (currentView === 'home') {
      return <Home onNavigate={handleNavigate} />;
    }
    if (currentView === 'login') {
      return <Login onNavigate={handleNavigate} />;
    }
    if (currentView === 'register') {
      return <Register onNavigate={handleNavigate} />;
    }

    // Protected routes requiring authentication
    if (!isAuthenticated) {
      return <Login onNavigate={handleNavigate} />;
    }

    if (currentView === 'artisan-dashboard') {
      return <ArtisanDashboard onNavigate={handleNavigate} />;
    }
    if (currentView === 'workflow-new') {
      return <ProductWorkflowWizard onNavigate={handleNavigate} />;
    }
    if (currentView === 'workflow-wizard') {
      return <ProductWorkflowWizard productId={viewData?.productId} onNavigate={handleNavigate} />;
    }
    if (currentView === 'buyer-dashboard') {
      return <BuyerDashboard onNavigate={handleNavigate} />;
    }
    if (currentView === 'inquiries') {
      return <InquiriesPage onNavigate={handleNavigate} />;
    }
    if (currentView === 'admin-dashboard') {
      return <AdminDashboard onNavigate={handleNavigate} />;
    }
    if (currentView === 'profile') {
      return <ProfilePage onNavigate={handleNavigate} />;
    }

    // Role-based default landing when route unrecognized
    if (user?.role === 'artisan') {
      return <ArtisanDashboard onNavigate={handleNavigate} />;
    }
    if (user?.role === 'buyer') {
      return <BuyerDashboard onNavigate={handleNavigate} />;
    }
    if (user?.role === 'admin') {
      return <AdminDashboard onNavigate={handleNavigate} />;
    }

    return <Home onNavigate={handleNavigate} />;
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-bg)' }}>
      <Navbar currentView={currentView} onNavigate={handleNavigate} />
      <main style={{ flex: 1 }}>
        {isLoading ? (
          <div style={{ minHeight: '60vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
            <div style={{ width: 48, height: 48, border: '4px solid #F7F4EE', borderTopColor: '#C85A32', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
            <p style={{ color: '#64748B', fontSize: '0.95rem', margin: 0 }}>Loading…</p>
            <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
          </div>
        ) : renderView()}
      </main>
      <footer style={{ background: '#1c1917', color: '#a8a29e', padding: '2.5rem 1.5rem', marginTop: 'auto', borderTop: '1px solid #292524' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', fontSize: '0.85rem' }}>
          <div>
            <strong style={{ color: '#fff', fontSize: '1rem' }}>KarigarConnect</strong> — AI-Powered Artisan Empowerment & Direct Market Linkage Ecosystem
          </div>
          <div>
            FastAPI Backend &middot; MongoDB Atlas &middot; Google Gemini SDK &middot; Dynamic Pricing &middot; Market Linkage
          </div>
        </div>
      </footer>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
