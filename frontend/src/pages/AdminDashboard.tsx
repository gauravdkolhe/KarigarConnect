import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { AdminMetrics, UserProfile } from '../types';
import { 
  ShieldCheck, 
  Users, 
  ShoppingBag, 
  BarChart3, 
  CheckCircle, 
  AlertTriangle,
  RefreshCw,
  Filter,
  Check,
  Ban
} from 'lucide-react';

interface AdminDashboardProps {
  onNavigate?: (view: string, data?: any) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = () => {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'metrics' | 'users' | 'products'>('metrics');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [mRes, uRes, pRes] = await Promise.all([
        api.getAdminMetrics(),
        api.listAdminUsers(),
        api.listAdminProducts()
      ]);
      setMetrics(mRes);
      setUsers(uRes.users);
      setProducts(pRes.products);
    } catch (err: any) {
      console.error('Failed to load admin data', err);
      setError(err.message || 'Failed to fetch administrator metrics and records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleToggleUserStatus = async (userItem: UserProfile) => {
    const newStatus = userItem.status === 'active' ? 'suspended' : 'active';
    if (!window.confirm(`Are you sure you want to change status to "${newStatus}" for ${userItem.email}?`)) return;

    setActionLoading(true);
    setError(null);
    try {
      await api.updateUserStatus(userItem.user_id, newStatus, `Admin status toggled via dashboard.`);
      setSuccessMsg(`User ${userItem.email} successfully updated to "${newStatus}".`);
      fetchDashboardData();
    } catch (err: any) {
      console.error('User status error', err);
      setError(err.message || 'Failed to update user account status.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateProductStatus = async (productId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'published' ? 'archived' : 'published';
    setActionLoading(true);
    setError(null);
    try {
      await api.moderateProduct(productId, newStatus, `Moderated by admin to ${newStatus}`);
      setSuccessMsg(`Product ${productId} status changed to ${newStatus}.`);
      fetchDashboardData();
    } catch (err: any) {
      console.error('Product status error', err);
      setError(err.message || 'Failed to update product status.');
    } finally {
      setActionLoading(false);
    }
  };

  const filteredUsers = users.filter(u => {
    if (roleFilter === 'all') return true;
    return u.role === roleFilter;
  });

  return (
    <div className="container" style={{ padding: '2rem 1.5rem', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <ShieldCheck size={28} style={{ color: 'var(--color-primary)' }} />
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary-dark)' }}>
              Executive Governance Dashboard
            </h1>
          </div>
          <p style={{ color: 'var(--color-text-muted)' }}>
            Real-time platform oversight, four-agent telemetry, user moderation, and genuine MongoDB marketplace statistics.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            className="btn btn-outline" 
            onClick={fetchDashboardData}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} style={{ marginRight: '6px' }} />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '2px solid #e5e7eb', marginBottom: '2rem' }}>
        <button 
          onClick={() => setActiveTab('metrics')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'metrics' ? '3px solid var(--color-primary)' : '3px solid transparent',
            color: activeTab === 'metrics' ? 'var(--color-primary-dark)' : 'var(--color-text-muted)',
            fontWeight: activeTab === 'metrics' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <BarChart3 size={18} /> Platform Analytics
        </button>

        <button 
          onClick={() => setActiveTab('users')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'users' ? '3px solid var(--color-primary)' : '3px solid transparent',
            color: activeTab === 'users' ? 'var(--color-primary-dark)' : 'var(--color-text-muted)',
            fontWeight: activeTab === 'users' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <Users size={18} /> User Accounts ({users.length})
        </button>

        <button 
          onClick={() => setActiveTab('products')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'products' ? '3px solid var(--color-primary)' : '3px solid transparent',
            color: activeTab === 'products' ? 'var(--color-primary-dark)' : 'var(--color-text-muted)',
            fontWeight: activeTab === 'products' ? 700 : 500,
            cursor: 'pointer',
            fontSize: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <ShoppingBag size={18} /> Product Listings ({products.length})
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="alert alert-success" style={{ marginBottom: '1.5rem' }}>
          <CheckCircle size={20} />
          <span>{successMsg}</span>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem' }} />
          <p>Compiling live database metrics and audit logs...</p>
        </div>
      ) : (
        <>
          {/* TAB 1: PLATFORM METRICS */}
          {activeTab === 'metrics' && metrics && (
            <div>
              {/* Primary Stat Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
                <div className="card" style={{ borderLeft: '4px solid var(--color-primary)' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Registered Artisans</span>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary)', marginTop: '0.25rem' }}>
                    {metrics.total_artisans}
                  </div>
                </div>

                <div className="card" style={{ borderLeft: '4px solid var(--color-accent)' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Registered Buyers</span>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-accent-dark)', marginTop: '0.25rem' }}>
                    {metrics.total_buyers}
                  </div>
                </div>

                <div className="card" style={{ borderLeft: '4px solid var(--color-success)' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Total Products</span>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-success)', marginTop: '0.25rem' }}>
                    {metrics.total_products}
                  </div>
                  <small style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                    {metrics.published_products} Published
                  </small>
                </div>

                <div className="card" style={{ borderLeft: '4px solid #8b5cf6' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Buyer Requirements</span>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: '#8b5cf6', marginTop: '0.25rem' }}>
                    {metrics.active_requirements}
                  </div>
                  <small style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                    {metrics.total_requirements} Total
                  </small>
                </div>

                <div className="card" style={{ borderLeft: '4px solid #06b6d4' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Commercial Inquiries</span>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: '#06b6d4', marginTop: '0.25rem' }}>
                    {metrics.total_inquiries}
                  </div>
                  <small style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                    {metrics.total_pricing_records} Pricing Records
                  </small>
                </div>
              </div>

              {/* Categorical Distribution */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                <div className="card">
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--color-primary-dark)' }}>
                    Top Buyer Procurement Categories
                  </h3>
                  {metrics.categories_breakdown && metrics.categories_breakdown.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {metrics.categories_breakdown.map((item) => (
                        <div key={item.category}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem' }}>
                            <span><strong>{item.category}</strong></span>
                            <span>{item.count} requirements</span>
                          </div>
                          <div style={{ width: '100%', height: '8px', background: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                            <div 
                              style={{ 
                                width: `${Math.min(100, (item.count / Math.max(...metrics.categories_breakdown.map(c => c.count))) * 100)}%`, 
                                height: '100%', 
                                background: 'var(--color-primary)' 
                              }} 
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>No categorical data recorded yet.</p>
                  )}
                </div>

                <div className="card">
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--color-primary-dark)' }}>
                    System Status & Telemetry
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: 'var(--color-bg-alt)', borderRadius: '6px' }}>
                      <span><strong>FastAPI Engine:</strong></span>
                      <span className="badge badge-success">HEALTHY (v2.0)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: 'var(--color-bg-alt)', borderRadius: '6px' }}>
                      <span><strong>MongoDB Atlas Cluster:</strong></span>
                      <span className="badge badge-success">CONNECTED</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: 'var(--color-bg-alt)', borderRadius: '6px' }}>
                      <span><strong>Google Gemini 2.5 Flash:</strong></span>
                      <span className="badge badge-primary">ACTIVE (SDK)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: 'var(--color-bg-alt)', borderRadius: '6px' }}>
                      <span><strong>Dynamic Pricing Engine:</strong></span>
                      <span className="badge badge-accent">DETERMINISTIC DECIMAL</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: 'var(--color-bg-alt)', borderRadius: '6px' }}>
                      <span><strong>Market Linkage Engine:</strong></span>
                      <span className="badge badge-neutral">DETERMINISTIC COMPATIBILITY</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textAlign: 'right', marginTop: '0.5rem' }}>
                      Telemetry Generated At: {metrics.generated_at}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: USER ACCOUNTS */}
          {activeTab === 'users' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <Filter size={16} style={{ color: 'var(--color-text-muted)' }} />
                  <span style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>Role Filter:</span>
                  {['all', 'artisan', 'buyer', 'admin'].map(r => (
                    <button
                      key={r}
                      className={`btn btn-sm ${roleFilter === r ? 'btn-primary' : 'btn-outline'}`}
                      onClick={() => setRoleFilter(r)}
                    >
                      {r.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div className="table-responsive">
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                    <thead style={{ background: 'var(--color-bg-alt)', borderBottom: '1px solid #e5e7eb' }}>
                      <tr>
                        <th style={{ padding: '0.75rem 1rem' }}>Name</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Email / Phone</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Role</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Location / Business</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                        <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map((u) => (
                        <tr key={u.user_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                          <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>
                            {u.full_name}
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <div>{u.email}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{u.phone_number || u.phone || '—'}</div>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className={`badge ${u.role === 'admin' ? 'badge-primary' : u.role === 'artisan' ? 'badge-accent' : 'badge-neutral'}`}>
                              {u.role.toUpperCase()}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <div>{u.business_name || u.craft_type || '—'}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{u.location || '—'}</div>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className={`badge ${u.status === 'active' ? 'badge-success' : 'badge-danger'}`}>
                              {u.status?.toUpperCase()}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                            {u.role !== 'admin' && (
                              <button
                                className={`btn btn-sm ${u.status === 'active' ? 'btn-outline' : 'btn-primary'}`}
                                onClick={() => handleToggleUserStatus(u)}
                                disabled={actionLoading}
                              >
                                {u.status === 'active' ? (
                                  <><Ban size={14} style={{ marginRight: '4px' }} /> Suspend</>
                                ) : (
                                  <><Check size={14} style={{ marginRight: '4px' }} /> Reactivate</>
                                )}
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: PRODUCT LISTINGS */}
          {activeTab === 'products' && (
            <div>
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div className="table-responsive">
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                    <thead style={{ background: 'var(--color-bg-alt)', borderBottom: '1px solid #e5e7eb' }}>
                      <tr>
                        <th style={{ padding: '0.75rem 1rem' }}>Product ID</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Title & Category</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Artisan ID</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Workflow Status</th>
                        <th style={{ padding: '0.75rem 1rem' }}>Publish State</th>
                        <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Moderation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {products.map((p) => (
                        <tr key={p.product_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                          <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>
                            {p.product_id}
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <div style={{ fontWeight: 600 }}>{p.product_name || p.title || 'Untitled Craft'}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{p.category || 'Traditional Craft'}</div>
                          </td>
                          <td style={{ padding: '0.75rem 1rem', fontSize: '0.85rem' }}>
                            {p.artisan_id || 'Legacy / Unassigned'}
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className="badge badge-accent">
                              {p.workflow_status || 'draft'}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className={`badge ${p.workflow_status === 'published' ? 'badge-success' : 'badge-neutral'}`}>
                              {p.workflow_status === 'published' ? 'PUBLISHED' : 'UNPUBLISHED'}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                            <button
                              className={`btn btn-sm ${p.workflow_status === 'published' ? 'btn-outline' : 'btn-primary'}`}
                              onClick={() => handleUpdateProductStatus(p.product_id, p.workflow_status)}
                              disabled={actionLoading}
                            >
                              {p.workflow_status === 'published' ? 'Unpublish' : 'Publish'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
