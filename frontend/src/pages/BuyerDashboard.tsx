import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import type { BuyerRequirement, ProductMatch } from '../types';
import { 
  ShoppingBag, 
  PlusCircle, 
  Search, 
  MapPin, 
  Calendar, 
  Layers, 
  Send, 
  CheckCircle2, 
  AlertCircle,
  DollarSign,
  Package
} from 'lucide-react';

interface BuyerDashboardProps {
  onNavigate?: (view: string, data?: any) => void;
}

export const BuyerDashboard: React.FC<BuyerDashboardProps> = () => {
  const { user } = useAuth();
  const [requirements, setRequirements] = useState<BuyerRequirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'requirements' | 'create' | 'matches'>('requirements');
  const [selectedReq, setSelectedReq] = useState<BuyerRequirement | null>(null);
  const [matches, setMatches] = useState<ProductMatch[]>([]);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Inquiry modal state
  const [inquiryModalOpen, setInquiryModalOpen] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<ProductMatch | null>(null);
  const [inquiryQuantity, setInquiryQuantity] = useState<number>(50);
  const [inquiryMessage, setInquiryMessage] = useState<string>('');
  const [sendingInquiry, setSendingInquiry] = useState(false);

  // New Requirement Form state
  const [formData, setFormData] = useState({
    requirement_id: `REQ-${Date.now().toString().slice(-6)}`,
    title: '',
    category: 'Home & Living',
    description: '',
    materials: 'Terracotta, Natural Clay',
    craft_types: 'Pottery, Clay Modeling',
    required_quantity: 100,
    min_budget: 15000,
    max_budget: 35000,
    delivery_location: user?.location || 'Mumbai, Maharashtra',
    deadline_days: 30,
    additional_specifications: 'Handcrafted authentic finish, uniform firing, eco-friendly packaging required.',
  });

  const fetchRequirements = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.listRequirements('active');
      setRequirements(res.requirements || []);
      if (res.requirements?.length > 0 && !selectedReq) {
        setSelectedReq(res.requirements[0]);
      }
    } catch (err: any) {
      console.error('Failed to load requirements', err);
      setError('Failed to fetch your sourcing requirements.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequirements();
  }, []);

  const handleSelectRequirement = async (req: BuyerRequirement) => {
    setSelectedReq(req);
    setActiveTab('matches');
    setLoadingMatches(true);
    setError(null);
    try {
      const res = await api.getBuyerMatches(req.requirement_id);
      setMatches(res.matches || []);
    } catch (err: any) {
      console.error('Failed to load matches', err);
      setError('Failed to retrieve matching artisan products.');
    } finally {
      setLoadingMatches(false);
    }
  };

  const handleCreateRequirement = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    try {
      const payload = {
        requirement_id: formData.requirement_id,
        buyer_id: user?.user_id || 'BUYER-001',
        buyer_name: user?.business_name || user?.full_name || 'Verified Enterprise Buyer',
        buyer_type: user?.buyer_type || 'Retailer',
        required_category: formData.category,
        requirement_title: formData.title,
        description: formData.description,
        required_keywords: formData.title.toLowerCase().split(' ').filter(Boolean),
        preferred_materials: formData.materials.split(',').map(m => m.trim()).filter(Boolean),
        preferred_craft_types: formData.craft_types.split(',').map(c => c.trim()).filter(Boolean),
        required_quantity: Number(formData.required_quantity),
        minimum_budget: Number(formData.min_budget),
        maximum_budget: Number(formData.max_budget),
        currency: 'INR',
        delivery_location: formData.delivery_location,
        delivery_deadline_days: Number(formData.deadline_days),
      };

      await api.createRequirement(payload);
      setSuccessMsg('Sourcing requirement published successfully!');
      setFormData({
        requirement_id: `REQ-${Date.now().toString().slice(-6)}`,
        title: '',
        category: 'Home & Living',
        description: '',
        materials: 'Terracotta, Natural Clay',
        craft_types: 'Pottery, Clay Modeling',
        required_quantity: 100,
        min_budget: 15000,
        max_budget: 35000,
        delivery_location: user?.location || 'Mumbai, Maharashtra',
        deadline_days: 30,
        additional_specifications: '',
      });
      fetchRequirements();
      setActiveTab('requirements');
    } catch (err: any) {
      console.error('Failed to create requirement', err);
      setError(err.message || 'Failed to publish requirement.');
    }
  };

  const handleOpenInquiry = (match: ProductMatch) => {
    setSelectedMatch(match);
    setInquiryQuantity(match.buyer_summary?.required_quantity || selectedReq?.required_quantity || 50);
    setInquiryMessage(`Hello, we are interested in sourcing your "${match.product_title || 'handcrafted product'}" for our current procurement mandate.`);
    setInquiryModalOpen(true);
  };

  const handleSendInquiry = async () => {
    if (!selectedMatch) return;
    setSendingInquiry(true);
    setError(null);
    try {
      await api.submitInquiry({
        product_id: selectedMatch.product_id,
        product_name: selectedMatch.product_title,
        requirement_id: selectedReq?.requirement_id,
        quantity_requested: inquiryQuantity,
        target_price_per_unit: selectedMatch.artisan_summary?.unit_price ? Number(selectedMatch.artisan_summary.unit_price) : undefined,
        delivery_destination: selectedReq?.delivery_location || user?.location || 'Mumbai',
        message: inquiryMessage,
      });
      setSuccessMsg(`Inquiry successfully sent to the artisan of ${selectedMatch.product_title}!`);
      setInquiryModalOpen(false);
      setSelectedMatch(null);
    } catch (err: any) {
      console.error('Inquiry send error', err);
      setError(err.message || 'Failed to dispatch inquiry.');
    } finally {
      setSendingInquiry(false);
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1.5rem', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary-dark)' }}>
            Buyer Procurement Portal
          </h1>
          <p style={{ color: 'var(--color-text-muted)' }}>
            Connect with verified traditional artisans, view deterministic matches, and dispatch formal sourcing inquiries.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            className={`btn ${activeTab === 'requirements' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('requirements')}
          >
            <ShoppingBag size={18} style={{ marginRight: '6px' }} />
            My Sourcing Requirements ({requirements.length})
          </button>
          <button 
            className={`btn ${activeTab === 'create' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('create')}
          >
            <PlusCircle size={18} style={{ marginRight: '6px' }} />
            Post Sourcing Requirement
          </button>
        </div>
      </div>

      {/* Notifications / Alerts */}
      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="alert alert-success" style={{ marginBottom: '1.5rem' }}>
          <CheckCircle2 size={20} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* TAB 1: SOURCING REQUIREMENTS LIST */}
      {activeTab === 'requirements' && (
        <div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '4rem' }}>
              <div className="spinner" style={{ margin: '0 auto 1rem' }} />
              <p>Loading sourcing requirements from MongoDB...</p>
            </div>
          ) : requirements.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
              <Package size={48} style={{ color: 'var(--color-primary)', margin: '0 auto 1rem' }} />
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>No Sourcing Requirements Found</h3>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
                Create your first procurement mandate to activate the Market Linkage Agent and find matching artisan products.
              </p>
              <button className="btn btn-primary" onClick={() => setActiveTab('create')}>
                Create Requirement
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.5rem' }}>
              {requirements.map((req) => (
                <div key={req.requirement_id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                      <span className="badge badge-primary">{req.required_category}</span>
                      <span className={`badge ${req.requirement_status === 'active' ? 'badge-success' : 'badge-neutral'}`}>
                        {req.requirement_status?.toUpperCase()}
                      </span>
                    </div>

                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--color-primary-dark)' }}>
                      {req.requirement_title}
                    </h3>
                    <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '1rem', lineClamp: 2 }}>
                      {req.description}
                    </p>

                    <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', color: 'var(--color-text-main)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Package size={15} style={{ color: 'var(--color-primary)' }} />
                        <span><strong>Quantity Required:</strong> {req.required_quantity} units</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <DollarSign size={15} style={{ color: 'var(--color-primary)' }} />
                        <span><strong>Budget:</strong> ₹{req.minimum_budget?.toLocaleString()} - ₹{req.maximum_budget?.toLocaleString()}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <MapPin size={15} style={{ color: 'var(--color-primary)' }} />
                        <span><strong>Destination:</strong> {req.delivery_location}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Calendar size={15} style={{ color: 'var(--color-primary)' }} />
                        <span><strong>Timeline:</strong> Within {req.delivery_deadline_days} days</span>
                      </div>
                    </div>

                    <div style={{ marginTop: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                      {req.preferred_materials?.map((m: string, idx: number) => (
                        <span key={idx} style={{ fontSize: '0.75rem', background: '#f3f4f6', padding: '2px 8px', borderRadius: '4px' }}>
                          {m}
                        </span>
                      ))}
                      {req.preferred_craft_types?.map((c: string, idx: number) => (
                        <span key={idx} style={{ fontSize: '0.75rem', background: 'var(--color-accent-light)', color: 'var(--color-primary-dark)', padding: '2px 8px', borderRadius: '4px' }}>
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
                    <button 
                      className="btn btn-primary" 
                      style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
                      onClick={() => handleSelectRequirement(req)}
                    >
                      <Search size={16} />
                      View Matching Artisan Crafts
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: POST SOURCING REQUIREMENT */}
      {activeTab === 'create' && (
        <div className="card" style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--color-primary-dark)' }}>
            Post New Sourcing Requirement
          </h2>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
            Specify your technical craft specifications, budget parameters, and delivery constraints.
          </p>

          <form onSubmit={handleCreateRequirement}>
            <div className="form-group">
              <label className="form-label">Requirement Title *</label>
              <input 
                type="text" 
                className="form-control" 
                placeholder="e.g., Bulk Terracotta Water Pitchers & Kulhads"
                value={formData.title}
                onChange={e => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Category *</label>
                <select 
                  className="form-control"
                  value={formData.category}
                  onChange={e => setFormData({ ...formData, category: e.target.value })}
                >
                  <option value="Home & Living">Home & Living</option>
                  <option value="Art & Collectibles">Art & Collectibles</option>
                  <option value="Apparel & Textiles">Apparel & Textiles</option>
                  <option value="Kitchen & Dining">Kitchen & Dining</option>
                  <option value="Jewelry & Accessories">Jewelry & Accessories</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Required Total Quantity *</label>
                <input 
                  type="number" 
                  className="form-control"
                  value={formData.required_quantity}
                  onChange={e => setFormData({ ...formData, required_quantity: Number(e.target.value) })}
                  min={1}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Detailed Requirement Description</label>
              <textarea 
                className="form-control" 
                rows={3}
                placeholder="Detail craftsmanship criteria, dimensional requirements, color palettes, and finishing standards..."
                value={formData.description}
                onChange={e => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Accepted Materials (comma separated)</label>
                <input 
                  type="text" 
                  className="form-control"
                  placeholder="e.g. Clay, Terracotta, Natural Glaze"
                  value={formData.materials}
                  onChange={e => setFormData({ ...formData, materials: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Craft Techniques (comma separated)</label>
                <input 
                  type="text" 
                  className="form-control"
                  placeholder="e.g. Pottery, Wheel Throwing, Hand Painting"
                  value={formData.craft_types}
                  onChange={e => setFormData({ ...formData, craft_types: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Minimum Total Budget (₹) *</label>
                <input 
                  type="number" 
                  className="form-control"
                  value={formData.min_budget}
                  onChange={e => setFormData({ ...formData, min_budget: Number(e.target.value) })}
                  min={100}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Maximum Total Budget (₹) *</label>
                <input 
                  type="number" 
                  className="form-control"
                  value={formData.max_budget}
                  onChange={e => setFormData({ ...formData, max_budget: Number(e.target.value) })}
                  min={100}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Delivery Destination *</label>
                <input 
                  type="text" 
                  className="form-control"
                  placeholder="City, State"
                  value={formData.delivery_location}
                  onChange={e => setFormData({ ...formData, delivery_location: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Delivery Deadline (Days) *</label>
                <input 
                  type="number" 
                  className="form-control"
                  value={formData.deadline_days}
                  onChange={e => setFormData({ ...formData, deadline_days: Number(e.target.value) })}
                  min={1}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
              <button type="button" className="btn btn-outline" onClick={() => setActiveTab('requirements')}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Publish Sourcing Requirement
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TAB 3: MATCHING ARTISAN PRODUCTS */}
      {activeTab === 'matches' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span className="badge badge-primary" style={{ marginBottom: '0.25rem' }}>
                Requirement: {selectedReq?.requirement_id}
              </span>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--color-primary-dark)' }}>
                Matching Products for: "{selectedReq?.requirement_title}"
              </h2>
            </div>
            <button className="btn btn-outline" onClick={() => setActiveTab('requirements')}>
              &larr; Back to All Requirements
            </button>
          </div>

          {loadingMatches ? (
            <div style={{ textAlign: 'center', padding: '4rem' }}>
              <div className="spinner" style={{ margin: '0 auto 1rem' }} />
              <p>Deterministic Market Linkage Agent is evaluating inventory feasibility and pricing...</p>
            </div>
          ) : matches.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
              <Layers size={48} style={{ color: 'var(--color-accent)', margin: '0 auto 1rem' }} />
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>No Compatible Matches Found</h3>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                No active artisan inventory currently satisfies this requirement's craft, budget, and delivery parameters.
              </p>
              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                Try adjusting your budget range or delivery timeframe to expand matching opportunities.
              </p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.5rem' }}>
              {matches.map((m) => (
                <div key={m.product_id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    {/* Header with match score */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                      <span className="badge badge-accent">
                        Score: {m.match_score.toFixed(0)}% ({m.match_category})
                      </span>
                      <span className="badge badge-neutral">ID: {m.product_id}</span>
                    </div>

                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-primary-dark)', marginBottom: '0.5rem' }}>
                      {m.product_title || `Product ${m.product_id}`}
                    </h3>

                    {/* Artisan public profile (protected) */}
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                      <strong>Lead Time:</strong> {m.artisan_summary?.lead_time_days ?? 'N/A'} days
                    </div>

                    {/* Metrics Breakdown */}
                    <div style={{ background: 'var(--color-bg-alt)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                        <span>Recommended Unit Price:</span>
                        <strong>₹{m.artisan_summary?.unit_price || 'N/A'}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                        <span>Available Stock:</span>
                        <strong>{m.artisan_summary?.available_quantity ?? 'Inquire'} units</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Delivery Feasibility:</span>
                        <strong style={{ color: m.compatibility?.delivery ? 'var(--color-success)' : 'var(--color-danger)' }}>
                          {m.compatibility?.delivery ? 'Satisfied' : 'Tight Timeline'}
                        </strong>
                      </div>
                    </div>

                    {/* Recommendation */}
                    {m.recommendation && (
                      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-main)', fontStyle: 'italic', marginBottom: '1rem', borderLeft: '3px solid var(--color-primary)', paddingLeft: '0.5rem' }}>
                        "{m.recommendation}"
                      </p>
                    )}

                    {/* Warnings */}
                    {m.warnings && m.warnings.length > 0 && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-warning)', marginBottom: '1rem' }}>
                        {m.warnings.map((w: string, idx: number) => (
                          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <AlertCircle size={12} />
                            <span>{w}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
                    <button 
                      className="btn btn-primary" 
                      style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
                      onClick={() => handleOpenInquiry(m)}
                    >
                      <Send size={16} />
                      Send Sourcing Inquiry
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SOURCING INQUIRY MODAL */}
      {inquiryModalOpen && selectedMatch && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--color-primary-dark)' }}>
              Dispatch Inquiry to Artisan
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1.25rem' }}>
              Target Product: <strong>{selectedMatch.product_title || selectedMatch.product_id}</strong>
            </p>

            <div className="form-group">
              <label className="form-label">Procurement Quantity Needed</label>
              <input 
                type="number" 
                className="form-control"
                value={inquiryQuantity}
                onChange={e => setInquiryQuantity(Number(e.target.value))}
                min={1}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Offered Unit Target Price (₹)</label>
              <input 
                type="text" 
                className="form-control"
                value={selectedMatch.artisan_summary?.unit_price || 'Standard'}
                disabled
              />
              <small style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                Based on artisan's calculated Dynamic Pricing recommendation.
              </small>
            </div>

            <div className="form-group">
              <label className="form-label">Direct Message / Specifications to Artisan</label>
              <textarea 
                className="form-control" 
                rows={4}
                value={inquiryMessage}
                onChange={e => setInquiryMessage(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
              <button 
                type="button" 
                className="btn btn-outline" 
                onClick={() => setInquiryModalOpen(false)}
                disabled={sendingInquiry}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={handleSendInquiry}
                disabled={sendingInquiry}
              >
                {sendingInquiry ? 'Sending...' : 'Send Formal Inquiry'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
