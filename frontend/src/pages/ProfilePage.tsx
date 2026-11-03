import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

interface ProfilePageProps {
  onNavigate?: (view: string, data?: any) => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = () => {
  const { user, updateProfile } = useAuth();
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone_number || user?.phone || '',
    location: user?.location || '',
    business_name: user?.business_name || '',
    craft_type: user?.craft_type || '',
    workshop_location: user?.workshop_location || '',
    bio: user?.short_bio || user?.bio || '',
    buyer_type: user?.buyer_type || '',
  });

  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setError(null);
    try {
      await updateProfile(formData);
      setSuccessMsg('Your profile has been successfully updated.');
    } catch (err: any) {
      console.error('Profile update error', err);
      setError(err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1.5rem', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary-dark)' }}>
          Profile Settings
        </h1>
        <p style={{ color: 'var(--color-text-muted)' }}>
          Manage your verified credentials, workshop specifications, and public commerce identity.
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
          <CheckCircle2 size={20} />
          <span>{successMsg}</span>
        </div>
      )}

      <div className="card" style={{ padding: '2rem' }}>
        {/* Role & Verification Badge Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '1.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'var(--color-primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: 700 }}>
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>{user?.full_name}</h3>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{user?.email}</div>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span className={`badge ${user?.role === 'admin' ? 'badge-primary' : user?.role === 'artisan' ? 'badge-accent' : 'badge-neutral'}`}>
              {user?.role?.toUpperCase()} ACCOUNT
            </span>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-success)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
              <ShieldCheck size={14} /> Verified Profile
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Full Legal Name</label>
            <input 
              type="text" 
              className="form-control"
              value={formData.full_name}
              onChange={e => setFormData({ ...formData, full_name: e.target.value })}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input 
                type="email" 
                className="form-control"
                value={user?.email || ''}
                disabled
              />
              <small style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                Primary login identifier cannot be altered.
              </small>
            </div>

            <div className="form-group">
              <label className="form-label">Contact Phone Number</label>
              <input 
                type="text" 
                className="form-control"
                value={formData.phone}
                onChange={e => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Geographic Location (City, State)</label>
              <input 
                type="text" 
                className="form-control"
                value={formData.location}
                onChange={e => setFormData({ ...formData, location: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Business / Studio / Company Name</label>
              <input 
                type="text" 
                className="form-control"
                value={formData.business_name}
                onChange={e => setFormData({ ...formData, business_name: e.target.value })}
              />
            </div>
          </div>

          {/* Artisan specific fields */}
          {user?.role === 'artisan' && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Primary Craft Discipline</label>
                  <input 
                    type="text" 
                    className="form-control"
                    placeholder="e.g. Blue Pottery, Zari Embroidery"
                    value={formData.craft_type}
                    onChange={e => setFormData({ ...formData, craft_type: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Workshop / Studio Location</label>
                  <input 
                    type="text" 
                    className="form-control"
                    placeholder="e.g. Sanganer Workshop, Jaipur"
                    value={formData.workshop_location}
                    onChange={e => setFormData({ ...formData, workshop_location: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Artisan Heritage & Craft Bio</label>
                <textarea 
                  className="form-control"
                  rows={3}
                  placeholder="Share your master crafting lineage, awards, techniques, and heritage story..."
                  value={formData.bio}
                  onChange={e => setFormData({ ...formData, bio: e.target.value })}
                />
              </div>
            </>
          )}

          {/* Buyer specific fields */}
          {user?.role === 'buyer' && (
            <div className="form-group">
              <label className="form-label">Buyer Sourcing Classification</label>
              <select 
                className="form-control"
                value={formData.buyer_type}
                onChange={e => setFormData({ ...formData, buyer_type: e.target.value })}
              >
                <option value="Retailer">Retailer / Boutique</option>
                <option value="Wholesaler">Wholesaler / Bulk Distributor</option>
                <option value="Exporter">International Exporter</option>
                <option value="Hospitality">Hospitality / Interior Designer</option>
                <option value="Corporate">Corporate Gifting Partner</option>
              </select>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Profile Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
