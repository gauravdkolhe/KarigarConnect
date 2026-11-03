import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Building, ShieldAlert, Sparkles } from 'lucide-react';

interface RegisterProps {
  onNavigate: (view: string) => void;
}

export const Register: React.FC<RegisterProps> = ({ onNavigate }) => {
  const { register } = useAuth();
  const [role, setRole] = useState<'artisan' | 'buyer'>('artisan');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [location, setLocation] = useState('');
  const [businessName, setBusinessName] = useState('');

  // Artisan fields
  const [craftType, setCraftType] = useState('');
  const [productCategories, setProductCategories] = useState('');
  const [bio, setBio] = useState('');

  // Buyer fields
  const [buyerType, setBuyerType] = useState('Retailer');
  const [procurementInterests, setProcurementInterests] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const payload: any = {
        full_name: fullName,
        email,
        password,
        role,
        phone: phone || undefined,
        location: location || undefined,
        business_name: businessName || undefined,
      };

      if (role === 'artisan') {
        payload.craft_type = craftType || undefined;
        payload.product_categories = productCategories
          ? productCategories.split(',').map((s) => s.trim()).filter(Boolean)
          : [];
        payload.bio = bio || undefined;
      } else {
        payload.buyer_type = buyerType;
        payload.procurement_interests = procurementInterests
          ? procurementInterests.split(',').map((s) => s.trim()).filter(Boolean)
          : [];
      }

      await register(payload);

      if (role === 'artisan') {
        onNavigate('artisan-dashboard');
      } else {
        onNavigate('buyer-dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please check your details.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '640px', margin: '2rem auto', padding: '0 1rem' }}>
      <div className="card" style={{ padding: '2.5rem 2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <h2 style={{ fontSize: '1.75rem' }}>Join KarigarConnect</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
            Choose your account type and start digitizing traditional crafts
          </p>
        </div>

        {/* Role Selector Tabs */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.75rem',
            marginBottom: '1.75rem',
            background: 'var(--color-bg-subtle)',
            padding: '0.4rem',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <button
            type="button"
            className="btn"
            style={{
              background: role === 'artisan' ? 'var(--color-primary)' : 'transparent',
              color: role === 'artisan' ? 'white' : 'var(--color-text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '0.6rem',
            }}
            onClick={() => setRole('artisan')}
          >
            <Sparkles size={16} />
            <span>I am an Artisan / Weaver</span>
          </button>
          <button
            type="button"
            className="btn"
            style={{
              background: role === 'buyer' ? 'var(--color-primary)' : 'transparent',
              color: role === 'buyer' ? 'white' : 'var(--color-text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '0.6rem',
            }}
            onClick={() => setRole('buyer')}
          >
            <Building size={16} />
            <span>I am a Sourcing Buyer</span>
          </button>
        </div>

        {error && (
          <div
            style={{
              background: 'var(--color-danger-bg)',
              color: 'var(--color-danger)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1.5rem',
            }}
          >
            <ShieldAlert size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Full Name *</label>
              <input
                type="text"
                className="form-control"
                required
                placeholder="Ramesh Kumar"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Email Address *</label>
              <input
                type="email"
                className="form-control"
                required
                placeholder="ramesh@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Password *</label>
              <input
                type="password"
                className="form-control"
                required
                placeholder="Min 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Contact Phone</label>
              <input
                type="tel"
                className="form-control"
                placeholder="+91-9876543210"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Location (City, State)</label>
              <input
                type="text"
                className="form-control"
                placeholder="Guwahati, Assam"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Workshop / Business Name</label>
              <input
                type="text"
                className="form-control"
                placeholder="Brahmaputra Bamboo Crafts"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
              />
            </div>
          </div>

          {/* Role-Specific Fields */}
          {role === 'artisan' ? (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Primary Craft Technique</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Bamboo Weaving, Pottery"
                    value={craftType}
                    onChange={(e) => setCraftType(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Product Categories (comma-separated)</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Home Decor, Storage, Tableware"
                    value={productCategories}
                    onChange={(e) => setProductCategories(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Artisan Story / Workshop Background</label>
                <textarea
                  className="form-control"
                  rows={3}
                  placeholder="Tell buyers about your craft heritage, materials used, and master crafting experience..."
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                />
              </div>
            </>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Buyer Entity Type</label>
                  <select
                    className="form-control"
                    value={buyerType}
                    onChange={(e) => setBuyerType(e.target.value)}
                  >
                    <option value="Retailer">Retailer / Boutique</option>
                    <option value="Wholesaler">Wholesaler</option>
                    <option value="Distributor">Distributor</option>
                    <option value="Exporter">Exporter</option>
                    <option value="Hotel">Hotel / Hospitality</option>
                    <option value="Interior designer">Interior Designer</option>
                    <option value="Corporate buyer">Corporate Gifting</option>
                    <option value="Other business">Other Business</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Target Craft Categories</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Bamboo Storage, Terracotta"
                    value={procurementInterests}
                    onChange={(e) => setProcurementInterests(e.target.value)}
                  />
                </div>
              </div>
            </>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.8rem', marginTop: '1rem' }}
            disabled={isLoading}
          >
            {isLoading ? 'Creating Account...' : `Register as ${role === 'artisan' ? 'Artisan' : 'Buyer'}`}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
          Already have an account?{' '}
          <button
            onClick={() => onNavigate('login')}
            style={{ background: 'none', border: 'none', color: 'var(--color-primary)', fontWeight: 600, cursor: 'pointer' }}
          >
            Login Here
          </button>
        </p>
      </div>
    </div>
  );
};
