import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import type { Inquiry } from '../types';
import { 
  MessageSquare, 
  Send, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertCircle, 
  Package, 
  DollarSign, 
  User
} from 'lucide-react';

interface InquiriesPageProps {
  onNavigate: (view: string, data?: any) => void;
}

export const InquiriesPage: React.FC<InquiriesPageProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [inquiries, setInquiries] = useState<Inquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Response modal state
  const [selectedInquiry, setSelectedInquiry] = useState<Inquiry | null>(null);
  const [statusUpdate, setStatusUpdate] = useState<'replied' | 'accepted' | 'declined'>('replied');
  const [responseNotes, setResponseNotes] = useState('');
  const [updating, setUpdating] = useState(false);

  const fetchInquiries = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.listInquiries();
      setInquiries(res.inquiries || []);
    } catch (err: any) {
      console.error('Failed to load inquiries', err);
      setError('Unable to load inquiries. Ensure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInquiries();
  }, []);

  const handleOpenActionModal = (inq: Inquiry) => {
    setSelectedInquiry(inq);
    setStatusUpdate('replied');
    setResponseNotes(inq.artisan_response_note || '');
  };

  const handleSubmitResponse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInquiry) return;
    setUpdating(true);
    setError(null);
    try {
      await api.updateInquiryStatus(selectedInquiry.inquiry_id, statusUpdate, responseNotes);
      setSuccessMsg(`Inquiry ${selectedInquiry.inquiry_id} updated to status "${statusUpdate}"!`);
      setSelectedInquiry(null);
      fetchInquiries();
    } catch (err: any) {
      console.error('Update inquiry error', err);
      setError(err.message || 'Failed to update inquiry status.');
    } finally {
      setUpdating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'accepted':
        return <span className="badge badge-success"><CheckCircle size={12} style={{ marginRight: '4px' }} /> Accepted</span>;
      case 'declined':
        return <span className="badge badge-danger"><XCircle size={12} style={{ marginRight: '4px' }} /> Declined</span>;
      case 'replied':
        return <span className="badge badge-primary"><Send size={12} style={{ marginRight: '4px' }} /> Replied</span>;
      default:
        return <span className="badge badge-accent"><Clock size={12} style={{ marginRight: '4px' }} /> Pending</span>;
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1.5rem', maxWidth: '1280px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary-dark)' }}>
          Commercial Inquiries & Linkages
        </h1>
        <p style={{ color: 'var(--color-text-muted)' }}>
          {user?.role === 'artisan' 
            ? 'Review and respond to direct wholesale and procurement inquiries received from verified enterprise buyers.' 
            : 'Track the status and responses of procurement inquiries dispatched to craft artisans.'}
        </p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={20} />
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
          <p>Loading inquiries from MongoDB...</p>
        </div>
      ) : inquiries.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <MessageSquare size={48} style={{ color: 'var(--color-primary)', margin: '0 auto 1rem' }} />
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>No Inquiries Yet</h3>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
            {user?.role === 'artisan'
              ? 'When buyers discover your published craft products through Market Linkage, their formal inquiries will appear here.'
              : 'Browse matching artisan products in your Sourcing Requirements dashboard to dispatch inquiries.'}
          </p>
          {user?.role === 'buyer' && (
            <button className="btn btn-primary" onClick={() => onNavigate('buyer-dashboard')}>
              Go to Buyer Dashboard
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '1.5rem' }}>
          {inquiries.map((inq) => (
            <div key={inq.inquiry_id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
                    {inq.inquiry_id}
                  </span>
                  {getStatusBadge(inq.status)}
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                    Product Reference:
                  </div>
                  <strong style={{ fontSize: '1.1rem', color: 'var(--color-primary-dark)' }}>
                    {inq.product_name || `Product #${inq.product_id}`}
                  </strong>
                  {inq.requirement_id && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-accent-dark)' }}>
                      Against Sourcing Mandate: {inq.requirement_id}
                    </div>
                  )}
                </div>

                <div style={{ background: 'var(--color-bg-alt)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Package size={14} /> Requested Units:
                    </span>
                    <strong>{inq.quantity_requested} units</strong>
                  </div>
                  {inq.target_price_per_unit && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <DollarSign size={14} /> Target Unit Price:
                      </span>
                      <strong>₹{inq.target_price_per_unit.toLocaleString()}</strong>
                    </div>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <User size={14} /> From Buyer:
                    </span>
                    <strong>{inq.buyer_name || inq.buyer_id}</strong>
                  </div>
                </div>

                {/* Message Content */}
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                    Buyer's Message:
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--color-text-main)', background: '#fff', padding: '0.6rem', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                    "{inq.message}"
                  </p>
                </div>

                {/* Artisan response if present */}
                {inq.artisan_response_note && (
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-primary)', marginBottom: '0.25rem' }}>
                      Artisan's Response:
                    </div>
                    <p style={{ fontSize: '0.9rem', color: 'var(--color-text-main)', background: 'var(--color-accent-light)', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--color-accent)' }}>
                      "{inq.artisan_response_note}"
                    </p>
                  </div>
                )}
              </div>

              {/* Actions for Artisan */}
              {user?.role === 'artisan' && inq.status !== 'declined' && inq.status !== 'accepted' && (
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
                  <button 
                    className="btn btn-primary" 
                    style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
                    onClick={() => handleOpenActionModal(inq)}
                  >
                    Respond to Inquiry
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* RESPOND MODAL */}
      {selectedInquiry && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--color-primary-dark)' }}>
              Respond to Buyer Inquiry
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1.25rem' }}>
              Inquiry: {selectedInquiry.inquiry_id} | Product: #{selectedInquiry.product_id}
            </p>

            <form onSubmit={handleSubmitResponse}>
              <div className="form-group">
                <label className="form-label">Update Commercial Status</label>
                <select 
                  className="form-control"
                  value={statusUpdate}
                  onChange={(e: any) => setStatusUpdate(e.target.value)}
                >
                  <option value="replied">Reply with Clarifications / Counter-Offer</option>
                  <option value="accepted">Accept Inquiry & Initiate Order Planning</option>
                  <option value="declined">Decline Inquiry (Capacity / Technical Constraint)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Response Message & Commercial Terms</label>
                <textarea 
                  className="form-control" 
                  rows={4}
                  placeholder="Detail your production timeline, minimum batch availability, and delivery conditions..."
                  value={responseNotes}
                  onChange={e => setResponseNotes(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  onClick={() => setSelectedInquiry(null)}
                  disabled={updating}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={updating}
                >
                  {updating ? 'Submitting...' : 'Submit Response'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
