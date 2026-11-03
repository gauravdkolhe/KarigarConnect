import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, API_BASE } from '../services/api';
import {
  ArrowRight,
  Box,
  CheckCircle2,
  Clock,
  MessageSquare,
  PlusCircle,
  RefreshCw,
  Sparkles,
} from 'lucide-react';

interface ArtisanDashboardProps {
  onNavigate: (view: string, productId?: string) => void;
}

export const ArtisanDashboard: React.FC<ArtisanDashboardProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [products, setProducts] = useState<any[]>([]);
  const [inquiries, setInquiries] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [prodsRes, inqRes] = await Promise.all([
        api.listArtisanProducts(),
        api.listInquiries(),
      ]);
      setProducts(prodsRes.products || []);
      setInquiries(inqRes.inquiries || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load artisan dashboard data.');
    } finally {
      setIsLoading(false);
    }
  };

  const publishedCount = products.filter((p) => p.workflow_status === 'published').length;
  const inProgressCount = products.filter((p) => p.workflow_status !== 'published').length;
  const pendingInquiriesCount = inquiries.filter((i) => i.status === 'pending').length;

  return (
    <div>
      {/* Top Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h1 style={{ fontSize: '2rem' }}>Artisan Studio Dashboard</h1>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.95rem' }}>
            Welcome back, {user?.full_name}! Manage your crafts, pricing, and genuine buyer linkages.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-outline btn-sm" onClick={loadData}>
            <RefreshCw size={15} />
            <span>Refresh</span>
          </button>
          <button
            className="btn btn-primary"
            onClick={() => onNavigate('workflow-new')}
          >
            <PlusCircle size={18} />
            <span>Add New Craft</span>
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <Box size={24} />
          </div>
          <div>
            <div className="stat-val">{products.length}</div>
            <div className="stat-label">Total Craft Listings</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#ECFDF5', color: 'var(--color-success)' }}>
            <CheckCircle2 size={24} />
          </div>
          <div>
            <div className="stat-val">{publishedCount}</div>
            <div className="stat-label">Published & Active</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#FFFBEB', color: 'var(--color-warning)' }}>
            <Clock size={24} />
          </div>
          <div>
            <div className="stat-val">{inProgressCount}</div>
            <div className="stat-label">Workflows In-Progress</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#EFF6FF', color: '#2563EB' }}>
            <MessageSquare size={24} />
          </div>
          <div>
            <div className="stat-val">{pendingInquiriesCount}</div>
            <div className="stat-label">Pending Inquiries</div>
          </div>
        </div>
      </div>

      {/* Main Products List */}
      <div className="card" style={{ padding: '1.75rem' }}>
        <div className="card-header">
          <h3 style={{ fontSize: '1.25rem' }}>My Handcrafted Products</h3>
          <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
            {products.length} registered
          </span>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--color-text-muted)' }}>
            <RefreshCw size={24} className="spin" style={{ marginBottom: '0.5rem' }} />
            <p>Loading your products...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-danger)' }}>
            {error}
          </div>
        ) : products.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'var(--color-primary-light)',
                color: 'var(--color-primary)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
              }}
            >
              <Sparkles size={28} />
            </div>
            <h4 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>No Crafts Listed Yet</h4>
            <p style={{ color: 'var(--color-text-muted)', maxWidth: '440px', margin: '0 auto 1.5rem', fontSize: '0.9rem' }}>
              Upload your first artisan product to trigger AI image enhancement, bilingual cataloging, and market linkage.
            </p>
            <button
              className="btn btn-primary"
              onClick={() => onNavigate('workflow-new')}
            >
              <PlusCircle size={16} />
              <span>Start 7-Step Product Workflow</span>
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {products.map((p) => {
              const statusClass =
                p.workflow_status === 'published'
                  ? 'badge-success'
                  : p.workflow_status === 'draft'
                  ? 'badge-info'
                  : 'badge-warning';

              return (
                <div
                  key={p.product_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '1rem 1.25rem',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--color-bg-subtle)',
                    flexWrap: 'wrap',
                    gap: '1rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    {p.thumbnail_url ? (
                      <img
                        src={`${API_BASE}${p.thumbnail_url}`}
                        alt={p.product_name}
                        style={{
                          width: '56px',
                          height: '56px',
                          borderRadius: 'var(--radius-md)',
                          objectFit: 'cover',
                          border: '1px solid var(--color-border)',
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          width: '56px',
                          height: '56px',
                          borderRadius: 'var(--radius-md)',
                          background: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          border: '1px solid var(--color-border)',
                          color: 'var(--color-text-muted)',
                        }}
                      >
                        <Box size={24} />
                      </div>
                    )}

                    <div>
                      <h4 style={{ fontSize: '1.05rem', marginBottom: '0.25rem' }}>{p.product_name}</h4>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                        <span>ID: {p.product_id}</span>
                        {p.suggested_selling_price ? (
                          <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
                            ₹{Number(p.suggested_selling_price).toLocaleString('en-IN')}
                          </span>
                        ) : (
                          <span>Unpriced</span>
                        )}
                        <span>{p.steps_completed?.length || 0}/7 steps complete</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span className={`badge ${statusClass}`}>
                      {p.workflow_status.replace('_', ' ').toUpperCase()}
                    </span>

                    <button
                      className="btn btn-outline btn-sm"
                      onClick={() => onNavigate('workflow-wizard', p.product_id)}
                    >
                      <span>{p.workflow_status === 'published' ? 'Manage Craft' : 'Resume Workflow'}</span>
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
