import React, { useState } from 'react';
import { Plus, X, CheckCircle2 } from 'lucide-react';

export interface Variation {
  variation_id: string;
  variation_type: string;
  label: string;
  price_adjustment: number;
  available_quantity: number;
  emoji: string;
}

interface VariationPickerProps {
  basePrice: number;
  variations: Variation[];
  onChange: (variations: Variation[]) => void;
}

// Pre-made chips per category
const PRESETS: Record<string, Array<{ label: string; emoji: string }>> = {
  size: [
    { label: 'Small',  emoji: '🔹' },
    { label: 'Medium', emoji: '🔷' },
    { label: 'Large',  emoji: '🔵' },
    { label: 'XL',     emoji: '🟦' },
    { label: 'XXL',    emoji: '⬛' },
    { label: '6 inch', emoji: '📏' },
    { label: '8 inch', emoji: '📏' },
    { label: '10 inch',emoji: '📏' },
    { label: '12 inch',emoji: '📏' },
  ],
  color: [
    { label: 'Natural', emoji: '🤍' },
    { label: 'Red',     emoji: '🔴' },
    { label: 'Blue',    emoji: '🔵' },
    { label: 'Green',   emoji: '🟢' },
    { label: 'Yellow',  emoji: '🟡' },
    { label: 'Black',   emoji: '⚫' },
    { label: 'White',   emoji: '⚪' },
    { label: 'Brown',   emoji: '🟤' },
    { label: 'Orange',  emoji: '🟠' },
    { label: 'Pink',    emoji: '🩷' },
  ],
  material: [
    { label: 'Cotton',  emoji: '🌿' },
    { label: 'Silk',    emoji: '✨' },
    { label: 'Jute',    emoji: '🪢' },
    { label: 'Wool',    emoji: '🧶' },
    { label: 'Bamboo',  emoji: '🎋' },
    { label: 'Clay',    emoji: '🏺' },
    { label: 'Wood',    emoji: '🪵' },
    { label: 'Brass',   emoji: '🔔' },
    { label: 'Leather', emoji: '👜' },
  ],
  type: [
    { label: 'Standard',   emoji: '📦' },
    { label: 'Premium',    emoji: '⭐' },
    { label: 'Deluxe',     emoji: '💎' },
    { label: 'Gift Boxed', emoji: '🎁' },
    { label: 'Set of 2',   emoji: '2️⃣' },
    { label: 'Set of 4',   emoji: '4️⃣' },
    { label: 'Set of 6',   emoji: '6️⃣' },
    { label: 'Customized', emoji: '🎨' },
  ],
};

const TYPES = [
  { key: 'size',     label: 'Size',     emoji: '📐' },
  { key: 'color',    label: 'Colour',   emoji: '🎨' },
  { key: 'material', label: 'Material', emoji: '🌿' },
  { key: 'type',     label: 'Type',     emoji: '📦' },
];

const uid = () => `VAR-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;

export const VariationPicker: React.FC<VariationPickerProps> = ({ basePrice, variations, onChange }) => {
  const [activeType, setActiveType]     = useState<string>('size');
  const [customLabel, setCustomLabel]   = useState('');
  const [customEmoji, setCustomEmoji]   = useState('');
  const [editingId, setEditingId]       = useState<string | null>(null);
  const [editPrice, setEditPrice]       = useState<string>('0');
  const [editQty, setEditQty]           = useState<string>('10');

  const isSelected = (label: string) => variations.some(v => v.label === label && v.variation_type === activeType);

  const togglePreset = (preset: { label: string; emoji: string }) => {
    if (isSelected(preset.label)) {
      onChange(variations.filter(v => !(v.label === preset.label && v.variation_type === activeType)));
    } else {
      onChange([...variations, {
        variation_id: uid(),
        variation_type: activeType,
        label: preset.label,
        emoji: preset.emoji,
        price_adjustment: 0,
        available_quantity: 10,
      }]);
    }
  };

  const addCustom = () => {
    const lbl = customLabel.trim();
    if (!lbl) return;
    if (variations.some(v => v.label === lbl && v.variation_type === activeType)) return;
    onChange([...variations, {
      variation_id: uid(),
      variation_type: activeType,
      label: lbl,
      emoji: customEmoji || '🔖',
      price_adjustment: 0,
      available_quantity: 10,
    }]);
    setCustomLabel('');
    setCustomEmoji('');
  };

  const removeVariation = (id: string) => onChange(variations.filter(v => v.variation_id !== id));

  const startEdit = (v: Variation) => {
    setEditingId(v.variation_id);
    setEditPrice(String(v.price_adjustment));
    setEditQty(String(v.available_quantity));
  };

  const saveEdit = () => {
    onChange(variations.map(v =>
      v.variation_id === editingId
        ? { ...v, price_adjustment: Number(editPrice) || 0, available_quantity: Number(editQty) || 10 }
        : v
    ));
    setEditingId(null);
  };

  return (
    <div>
      {/* Type tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {TYPES.map(t => (
          <button key={t.key} type="button"
            onClick={() => setActiveType(t.key)}
            style={{
              padding: '0.5rem 1rem', borderRadius: '999px', border: 'none', cursor: 'pointer',
              fontWeight: 600, fontSize: '0.88rem',
              background: activeType === t.key ? 'var(--color-primary)' : 'var(--color-bg-subtle)',
              color: activeType === t.key ? '#fff' : 'var(--color-text)',
              transition: 'all 0.15s',
            }}>
            {t.emoji} {t.label}
          </button>
        ))}
      </div>

      {/* Preset chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
        {(PRESETS[activeType] || []).map(p => {
          const sel = isSelected(p.label);
          return (
            <button key={p.label} type="button"
              onClick={() => togglePreset(p)}
              style={{
                padding: '0.55rem 1rem', borderRadius: '999px', cursor: 'pointer',
                border: sel ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                background: sel ? 'var(--color-primary-subtle,#F5F3FF)' : 'var(--color-bg)',
                color: sel ? 'var(--color-primary)' : 'var(--color-text)',
                fontWeight: sel ? 700 : 500, fontSize: '0.88rem',
                display: 'flex', alignItems: 'center', gap: '0.3rem',
                transition: 'all 0.15s',
              }}>
              <span>{p.emoji}</span>
              <span>{p.label}</span>
              {sel && <CheckCircle2 size={14} />}
            </button>
          );
        })}
      </div>

      {/* Custom input */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input
          className="form-control"
          placeholder={`Type custom ${activeType}…`}
          value={customLabel}
          onChange={e => setCustomLabel(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addCustom())}
          style={{ flex: 1, minWidth: '140px' }}
        />
        <input
          className="form-control"
          placeholder="Emoji (opt.)"
          value={customEmoji}
          onChange={e => setCustomEmoji(e.target.value)}
          style={{ width: '90px' }}
          maxLength={4}
        />
        <button type="button" className="btn btn-outline btn-sm"
          onClick={addCustom} disabled={!customLabel.trim()}
          style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <Plus size={15} /> Add
        </button>
      </div>

      {/* Selected variations list */}
      {variations.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <p style={{ margin: '0 0 0.3rem', fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-text-muted)' }}>
            {variations.length} variation{variations.length > 1 ? 's' : ''} added:
          </p>
          {variations.map(v => (
            <div key={v.variation_id} style={{
              display: 'flex', alignItems: 'center', gap: '0.6rem',
              padding: '0.6rem 0.85rem',
              background: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)', flexWrap: 'wrap',
            }}>
              <span style={{ fontSize: '1.1rem' }}>{v.emoji}</span>
              <span style={{ fontWeight: 700, flex: 1, minWidth: '80px' }}>{v.label}</span>
              <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', background: 'var(--color-bg)', padding: '0.1rem 0.4rem', borderRadius: 999, border: '1px solid var(--color-border)' }}>
                {v.variation_type}
              </span>

              {editingId === v.variation_id ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <span style={{ fontSize: '0.78rem' }}>₹ adjust:</span>
                    <input type="number" value={editPrice} onChange={e => setEditPrice(e.target.value)}
                      style={{ width: '70px', padding: '0.2rem 0.4rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', fontSize: '0.85rem' }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <span style={{ fontSize: '0.78rem' }}>Qty:</span>
                    <input type="number" value={editQty} onChange={e => setEditQty(e.target.value)}
                      style={{ width: '60px', padding: '0.2rem 0.4rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', fontSize: '0.85rem' }} min="0" />
                  </div>
                  <button type="button" onClick={saveEdit} className="btn btn-primary btn-sm" style={{ padding: '0.2rem 0.6rem', fontSize: '0.78rem' }}>Save</button>
                </>
              ) : (
                <>
                  {v.price_adjustment !== 0 && (
                    <span style={{ fontSize: '0.82rem', color: v.price_adjustment > 0 ? '#059669' : '#DC2626', fontWeight: 600 }}>
                      {v.price_adjustment > 0 ? '+' : ''}₹{v.price_adjustment}
                      {basePrice > 0 && <span style={{ fontWeight: 400, color: 'var(--color-text-muted)' }}> (₹{basePrice + v.price_adjustment})</span>}
                    </span>
                  )}
                  {v.price_adjustment === 0 && basePrice > 0 && (
                    <span style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>₹{basePrice}</span>
                  )}
                  <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>Qty: {v.available_quantity}</span>
                  <button type="button" onClick={() => startEdit(v)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.78rem', color: 'var(--color-primary)', fontWeight: 600, padding: '0.1rem 0.3rem' }}>
                    Edit
                  </button>
                  <button type="button" onClick={() => removeVariation(v.variation_id)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-danger)', padding: '0.1rem' }}>
                    <X size={15} />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

