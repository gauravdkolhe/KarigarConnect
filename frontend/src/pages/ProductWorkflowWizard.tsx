import React, { useEffect, useState, useRef } from 'react';
import { api, API_BASE } from '../services/api';
import type { ProductMatch, WorkflowState } from '../types';
import { VoiceInputButton } from '../components/VoiceInputButton';
import { VariationPicker, type Variation } from '../components/VariationPicker';
import {
  AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2,
  ChevronDown, ChevronUp, Layers, Loader2, Package, Sparkles,
  Star, Upload, Users, Wand2,
} from 'lucide-react';

interface Props {
  productId?: string;
  onNavigate: (view: string, data?: any) => void;
}

// ── Language → BCP-47 code ──────────────────────────────────────────────────
const LANG_CODE: Record<string, string> = {
  Hindi: 'hi-IN', Marathi: 'mr-IN', Bengali: 'bn-IN', Tamil: 'ta-IN',
  Telugu: 'te-IN', Kannada: 'kn-IN', Gujarati: 'gu-IN', Punjabi: 'pa-IN',
  Odia: 'or-IN', Assamese: 'as-IN', English: 'en-IN',
};

const LANGUAGES = Object.keys(LANG_CODE);

// ── Image style options ─────────────────────────────────────────────────────
const STYLES = [
  { id: 'studio_white',     name: 'Studio White',      dot: '#fff',     border: '#CBD5E1', tip: 'Standard for Amazon & Etsy' },
  { id: 'warm_heritage',    name: 'Warm Heritage',      dot: '#FAF8F5',  border: '#D6D3D1', tip: 'Best for wood, brass & clay' },
  { id: 'modern_minimalist',name: 'Modern Minimalist',  dot: '#F3F4F6',  border: '#9CA3AF', tip: 'Neutral studio with shadow' },
  { id: 'original',         name: 'Keep Original 📷',   dot: 'linear-gradient(135deg,#fde68a,#a7f3d0)', border: '#6EE7B7', tip: 'No AI edits — raw photo' },
];

// ── Stepper ─────────────────────────────────────────────────────────────────
const STEPS = [
  { num: 1, label: 'Photo', emoji: '📸' },
  { num: 2, label: 'Describe', emoji: '🎙️' },
  { num: 3, label: 'Published!', emoji: '✅' },
];

export const ProductWorkflowWizard: React.FC<Props> = ({ productId: initId, onNavigate }) => {
  const [step, setStep]             = useState(1);
  const [workflow, setWorkflow]     = useState<WorkflowState | null>(null);
  const [matches, setMatches]       = useState<ProductMatch[]>([]);
  const [busy, setBusy]             = useState(false);
  const [imgBusy, setImgBusy]       = useState(false);
  const [aiBusy, setAiBusy]         = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const [ok, setOk]                 = useState<string | null>(null);

  // Step 1 fields
  const [name, setName]             = useState('');
  const [category, setCategory]     = useState('Handicrafts');
  const [material, setMaterial]     = useState('');
  const [style, setStyle]           = useState('studio_white');
  const [file, setFile]             = useState<File | null>(null);
  const [preview, setPreview]       = useState<string | null>(null);

  // Step 2 fields
  const [language, setLanguage]     = useState('Hindi');
  const [spoken, setSpoken]         = useState('');
  const [costHint, setCostHint]     = useState('');
  const [priceHint, setPriceHint]   = useState('');

  // AI result
  const [aiReady, setAiReady]       = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showVariations, setShowVariations] = useState(false);
  const [variations, setVariations] = useState<Variation[]>([]);
  const [editTitle, setEditTitle]   = useState('');
  const [editDesc, setEditDesc]     = useState('');
  const [editKw, setEditKw]         = useState('');
  const [editMat, setEditMat]       = useState('');
  const [editPrice, setEditPrice]   = useState('');
  const [editQty, setEditQty]       = useState('20');
  const [editMoq, setEditMoq]       = useState('5');
  const [editLoc, setEditLoc]       = useState('India');

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── helpers ───────────────────────────────────────────────────────────────
  const err = (m: string) => { setError(m); setOk(null); };
  const win = (m: string) => { setOk(m);    setError(null); };

  const fillFromWorkflow = (w: WorkflowState) => {
    if (w.catalog) {
      setEditTitle(w.catalog.product_title || w.product_name);
      setEditDesc(w.catalog.description || '');
      setEditKw((w.catalog.keywords || []).join(', '));
      setEditMat(w.catalog.product_details?.material || '');
    }
    if (w.pricing?.suggested_selling_price)
      setEditPrice(String(w.pricing.suggested_selling_price));
    if (w.inventory) {
      setEditQty(String(w.inventory.available_quantity));
      setEditMoq(String(w.inventory.minimum_order_quantity));
      setEditLoc(w.inventory.location);
    }
    if (w.variations && w.variations.length > 0) {
      setVariations(w.variations.map(v => ({
        variation_id: v.variation_id,
        variation_type: v.variation_type,
        label: v.label,
        price_adjustment: v.price_adjustment,
        available_quantity: v.available_quantity,
        emoji: v.emoji || '🔖',
      })));
      setShowVariations(true);
    }
  };

  const loadMatches = async (pid: string) => {
    try { const r = await api.getProductMatches(pid, 20); setMatches(r.matches || []); }
    catch { /**/ }
  };

  useEffect(() => {
    if (!initId) return;
    (async () => {
      setBusy(true);
      try {
        const w = await api.getProductWorkflow(initId);
        setWorkflow(w); setName(w.product_name);
        if (w.workflow_status === 'published') { fillFromWorkflow(w); setAiReady(true); loadMatches(w.product_id); setStep(3); }
        else if (w.catalog)                    { fillFromWorkflow(w); setAiReady(true); setStep(2); }
        else if (w.images.length > 0)          { setStep(2); }
      } catch (e: any) { err(e.message || 'Failed to load product.'); }
      finally { setBusy(false); }
    })();
  }, [initId]);

  // ── STEP 1 ─────────────────────────────────────────────────────────────────
  const pickFile = (f: File) => {
    setFile(f);
    const r = new FileReader();
    r.onload = (e) => setPreview(e.target?.result as string);
    r.readAsDataURL(f);
  };

  const handleStep1 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { err('Please enter a product name.'); return; }
    setBusy(true); setError(null);
    try {
      const draft = await api.createProductDraft({
        product_name: name, category,
        initial_material: material || 'Handcraft',
        initial_craft_type: 'Traditional',
      });
      let w = draft;
      if (file) {
        setImgBusy(true);
        await api.uploadProductImage(draft.product_id, file, style);
        w = await api.getProductWorkflow(draft.product_id);
        setImgBusy(false);
        win('✨ Photo processed! Now describe your craft.');
      } else {
        win('Draft created. Now describe your craft.');
      }
      setWorkflow(w);
      setStep(2);
    } catch (e: any) { err(e.message || 'Failed. Please try again.'); }
    finally { setBusy(false); setImgBusy(false); }
  };

  // ── STEP 2 — Quick Assist ─────────────────────────────────────────────────
  const handleQuickAssist = async () => {
    if (!workflow) return;
    if (!spoken.trim()) { err('Please speak or type something about your craft first.'); return; }
    setAiBusy(true); setError(null);
    try {
      const w = await api.quickAssist(workflow.product_id, {
        spoken_text: spoken, language,
        estimated_cost: costHint ? Number(costHint) : undefined,
        desired_price:  priceHint ? Number(priceHint) : undefined,
      });
      setWorkflow(w);
      fillFromWorkflow(w);
      setAiReady(true);
      win('🤖 AI generated your listing! Set your price and publish.');
    } catch (e: any) { err(e.message || 'AI generation failed. Please try again.'); }
    finally { setAiBusy(false); }
  };

  // ── STEP 2 → 3 — One-click Publish ────────────────────────────────────────
  const handlePublish = async () => {
    if (!workflow) return;
    if (!editPrice || Number(editPrice) <= 0) { err('Please enter a selling price (₹).'); return; }
    setBusy(true); setError(null);
    try {
      const safeTitle = editTitle.trim() || name;
      const safeDesc  = editDesc.trim().length >= 5
        ? editDesc.trim()
        : `Handcrafted ${safeTitle} — authentic artisan product made with care.`;
      const safeKw = editKw.split(',').map(k => k.trim()).filter(Boolean);

      const w = await api.oneClickApprove(workflow.product_id, {
        product_title: safeTitle,
        description:   safeDesc,
        keywords:      safeKw,
        material:      editMat || material || 'Handcraft',
        suggested_price:      Number(editPrice),
        available_quantity:   Number(editQty) || 20,
        minimum_order_quantity: Number(editMoq) || 5,
        location:      editLoc || 'India',
      });

      // Save variations if artisan added any
      if (variations.length > 0) {
        try {
          await api.saveVariations(workflow.product_id, variations);
        } catch (vErr) {
          console.warn('Could not save variations:', vErr);
        }
      }

      setWorkflow(w);
      await loadMatches(w.product_id);
      win('🎉 Your product is live on the B2B marketplace!');
      setStep(3);
    } catch (e: any) { err(e.message || 'Publish failed. Please try again.'); }
    finally { setBusy(false); }
  };

  // ── RESET ─────────────────────────────────────────────────────────────────
  const reset = () => {
    setStep(1); setWorkflow(null); setName(''); setMaterial(''); setFile(null);
    setPreview(null); setSpoken(''); setAiReady(false); setShowAdvanced(false);
    setShowVariations(false); setVariations([]);
    setEditTitle(''); setEditDesc(''); setEditKw(''); setEditMat(''); setEditPrice('');
    setError(null); setOk(null); setMatches([]);
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', paddingBottom: '3rem' }}>

      {/* Back nav */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <button className="btn btn-outline btn-sm" onClick={() => onNavigate('artisan-dashboard')}>
          <ArrowLeft size={16} /><span>Back to Studio</span>
        </button>
        {workflow && <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
          ID: <strong>{workflow.product_id.slice(-8).toUpperCase()}</strong>
        </span>}
      </div>

      {/* ── Stepper ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '2rem' }}>
        {STEPS.map((s, i) => {
          const active = step === s.num;
          const done   = step > s.num;
          return (
            <React.Fragment key={s.num}>
              <div
                onClick={() => done && setStep(s.num)}
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem', cursor: done ? 'pointer' : 'default' }}
              >
                <div style={{
                  width: 52, height: 52, borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: done ? '1rem' : '1.4rem', fontWeight: 700,
                  background: done ? '#10B981' : active ? 'var(--color-primary)' : 'var(--color-bg-subtle)',
                  color: done || active ? '#fff' : 'var(--color-text-muted)',
                  border: active ? '3px solid var(--color-primary)' : done ? '3px solid #10B981' : '2px solid var(--color-border)',
                  boxShadow: active ? '0 0 0 5px rgba(124,58,237,0.15)' : 'none',
                  transition: 'all 0.25s',
                }}>
                  {done ? <CheckCircle2 size={24} /> : s.emoji}
                </div>
                <span style={{ fontSize: '0.75rem', fontWeight: active ? 700 : 500, color: active ? 'var(--color-primary)' : done ? '#10B981' : 'var(--color-text-muted)' }}>
                  {s.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div style={{ flex: 1, height: 3, maxWidth: 100, background: step > s.num ? '#10B981' : 'var(--color-border)', margin: '0 0.5rem 1.2rem', borderRadius: 2, transition: 'background 0.4s' }} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Alerts */}
      {error && <div style={{ background: 'var(--color-danger-bg)', color: 'var(--color-danger)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <AlertTriangle size={16} /><span>{error}</span>
      </div>}
      {ok && <div style={{ background: 'var(--color-success-bg)', color: 'var(--color-success)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <CheckCircle2 size={16} /><span>{ok}</span>
      </div>}

      {/* ══════════════════════════════════════════════════════════
           STEP 1 — PHOTO
      ══════════════════════════════════════════════════════════ */}
      {step === 1 && (
        <form onSubmit={handleStep1}>
          <div className="card" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>📸 Step 1: Upload Your Craft Photo</h2>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Share a photo — our AI will clean it up for the marketplace. Or keep your original photo as-is.
            </p>

            {/* Product name + mic */}
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label className="form-label" style={{ margin: 0 }}>Product Name *</label>
                <VoiceInputButton lang="en-IN" onTranscript={t => setName(p => p ? `${p} ${t}` : t)} placeholder="Listening..." />
              </div>
              <input className="form-control" required placeholder="e.g. Handwoven Bamboo Basket"
                value={name} onChange={e => setName(e.target.value)} />
            </div>

            {/* Category + Material */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Category</label>
                <input className="form-control" placeholder="e.g. Home Decor"
                  value={category} onChange={e => setCategory(e.target.value)} />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <label className="form-label" style={{ margin: 0 }}>Material</label>
                  <VoiceInputButton lang="en-IN" onTranscript={t => setMaterial(p => p ? `${p} ${t}` : t)} placeholder="Listening..." />
                </div>
                <input className="form-control" placeholder="e.g. Bamboo, Clay, Silk"
                  value={material} onChange={e => setMaterial(e.target.value)} />
              </div>
            </div>

            {/* Photo upload */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Upload size={15} color="var(--color-primary)" /> Craft Photo <span style={{ fontWeight: 400, color: 'var(--color-text-muted)' }}>(optional)</span>
              </label>

              {/* Clickable drop zone */}
              <div
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: '2px dashed var(--color-border)', borderRadius: 'var(--radius-lg)',
                  padding: preview ? 0 : '2rem', textAlign: 'center',
                  background: 'var(--color-bg-subtle)', cursor: 'pointer', overflow: 'hidden',
                  transition: 'border-color 0.2s',
                }}
              >
                {preview
                  ? <img src={preview} alt="preview" style={{ width: '100%', maxHeight: 260, objectFit: 'contain', display: 'block' }} />
                  : <>
                      <Upload size={32} color="var(--color-primary)" style={{ marginBottom: '0.5rem' }} />
                      <p style={{ margin: '0 0 0.2rem', fontWeight: 600 }}>Tap to choose a photo</p>
                      <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>JPG or PNG — max 10 MB</p>
                    </>
                }
              </div>
              <input ref={fileInputRef} type="file" accept="image/*" style={{ display: 'none' }}
                onChange={e => { const f = e.target.files?.[0]; if (f) pickFile(f); }} />

              {file && <p style={{ marginTop: '0.4rem', fontSize: '0.82rem', color: 'var(--color-primary)', fontWeight: 600 }}>
                ✓ {file.name} ({(file.size/1024/1024).toFixed(2)} MB)
              </p>}
            </div>

            {/* Style selector — only when photo selected */}
            {file && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label className="form-label">Photo Style</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: '0.6rem' }}>
                  {STYLES.map(s => (
                    <div key={s.id} onClick={() => setStyle(s.id)} style={{
                      border: style === s.id ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)', padding: '0.75rem', cursor: 'pointer',
                      background: style === s.id ? 'var(--color-primary-subtle,#F5F3FF)' : 'var(--color-bg)',
                      transition: 'all 0.15s',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.3rem' }}>
                        <span style={{ width: 14, height: 14, borderRadius: '50%', background: s.dot, border: `1px solid ${s.border}`, flexShrink: 0, display: 'inline-block' }} />
                        <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{s.name}</span>
                      </div>
                      <p style={{ fontSize: '0.74rem', color: 'var(--color-text-muted)', margin: 0 }}>{s.tip}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button type="submit" className="btn btn-primary" style={{ fontSize: '1rem', padding: '0.75rem 2rem' }} disabled={busy || imgBusy}>
              {busy || imgBusy
                ? <><Loader2 size={18} className="spin" /><span>{imgBusy ? 'Enhancing photo…' : 'Creating…'}</span></>
                : <><span>{file ? 'Use This Photo & Continue' : 'Continue Without Photo'}</span><ArrowRight size={18} /></>}
            </button>
          </div>
        </form>
      )}

      {/* ══════════════════════════════════════════════════════════
           STEP 2 — DESCRIBE & PUBLISH
      ══════════════════════════════════════════════════════════ */}
      {step === 2 && workflow && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

          {/* Photo thumbnail & Verification */}
          {workflow.images?.length > 0 && (
            <div className="card" style={{ padding: '1.25rem', border: '2px solid #BBF7D0', background: '#F0FDF4', borderRadius: 'var(--radius-lg)' }}>
              <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ position: 'relative', width: 110, height: 110, borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '2px solid #10B981', background: '#fff', boxShadow: '0 4px 10px rgba(0,0,0,0.08)', flexShrink: 0 }}>
                  <img src={`${API_BASE}${workflow.images[0].file_url}`} alt="Enhanced craft"
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                  <span style={{ position: 'absolute', bottom: 2, right: 2, background: '#10B981', color: '#fff', fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.35rem', borderRadius: 4 }}>
                    VERIFIED
                  </span>
                </div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.25rem' }}>
                    <CheckCircle2 size={18} color="#10B981" />
                    <span style={{ fontWeight: 800, color: '#166534', fontSize: '1rem' }}>Photo Enhanced & Verified in Studio</span>
                  </div>
                  <p style={{ margin: '0 0 0.5rem', fontSize: '0.82rem', color: '#166534', opacity: 0.9 }}>
                    Aesthetic studio lighting applied. Pure, clean framing for high-converting B2B buyer catalog displays.
                  </p>
                  <button type="button" className="btn btn-outline btn-xs" onClick={() => setStep(1)} style={{ fontSize: '0.75rem', background: '#fff' }}>
                    🔄 Change Photo / Style
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ── Voice / Describe card ── */}
          <div className="card" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>🎙️ Step 2: Describe Your Craft</h2>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Speak or type in <strong>any language</strong>. AI will write the product listing and suggest a fair price automatically.
            </p>

            {/* Language row */}
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
              <div className="form-group" style={{ flex: '0 0 160px', marginBottom: 0 }}>
                <label className="form-label">Language</label>
                <select className="form-control" value={language} onChange={e => setLanguage(e.target.value)}>
                  {LANGUAGES.map(l => <option key={l}>{l}</option>)}
                </select>
              </div>
              <p style={{ margin: '0 0 0.25rem', fontSize: '0.85rem', color: 'var(--color-text-muted)', alignSelf: 'flex-end' }}>
                Tap the big mic and speak in {language}
              </p>
            </div>

            {/* Big mic button centred */}
            <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
              <VoiceInputButton
                lang={LANG_CODE[language] || 'en-IN'}
                onTranscript={t => setSpoken(p => p ? `${p} ${t}` : t)}
                placeholder={`Listening in ${language}…`}
                large
              />
              <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
                Tap ▲ then speak — or just type below
              </p>
            </div>

            {/* Description textarea */}
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <textarea className="form-control" rows={4} style={{ resize: 'vertical' }}
                placeholder={`Describe your craft in ${language}. E.g. "यह बाँस की टोकरी हाथ से बुनी गई है…"`}
                value={spoken} onChange={e => setSpoken(e.target.value)} />
            </div>

            {/* Optional cost hints — collapsed by default */}
            <details style={{ marginBottom: '1.25rem' }}>
              <summary style={{ cursor: 'pointer', fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600, userSelect: 'none' }}>
                💰 Add cost / price hints (optional)
              </summary>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: '0.75rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Material cost (₹)</label>
                  <input type="number" className="form-control" placeholder="e.g. 200" min="0"
                    value={costHint} onChange={e => setCostHint(e.target.value)} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Your desired price (₹)</label>
                  <input type="number" className="form-control" placeholder="e.g. 850" min="0"
                    value={priceHint} onChange={e => setPriceHint(e.target.value)} />
                </div>
              </div>
            </details>

            <button type="button" className="btn btn-primary"
              style={{ width: '100%', fontSize: '1rem', padding: '0.85rem' }}
              onClick={handleQuickAssist}
              disabled={aiBusy || !spoken.trim()}
            >
              {aiBusy
                ? <><Loader2 size={18} className="spin" /><span>AI is writing your listing…</span></>
                : <><Wand2 size={18} /><span>Generate AI Description & Price ✨</span></>}
            </button>
          </div>

          {/* ── AI Result + Publish ── */}
          {aiReady && (
            <div className="card" style={{ padding: '2rem', border: '2px solid var(--color-primary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                <Sparkles size={20} color="var(--color-primary)" />
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>AI Generated — Check & Set Your Price</h3>
              </div>

              {/* AI preview (read-only summary) */}
              <div style={{ background: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '1.25rem', border: '1px solid var(--color-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                  <Sparkles size={16} color="var(--color-primary)" />
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-primary)' }}>
                    Auto-Translated into English for Global B2B Buyers
                  </span>
                </div>
                <p style={{ margin: '0 0 0.35rem', fontWeight: 800, fontSize: '1.05rem', color: 'var(--color-text)' }}>{editTitle}</p>
                <p style={{ margin: '0 0 0.5rem', fontSize: '0.88rem', color: 'var(--color-text)', lineHeight: 1.6 }}>
                  {editDesc}
                </p>
                {editKw && (
                  <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                    <strong>Keywords:</strong> {editKw}
                  </p>
                )}
              </div>

              {/* ── THE ONLY REQUIRED INPUT: Price ── */}
              <div style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 700, fontSize: '1rem', marginBottom: '0.5rem', color: '#166534' }}>
                  💰 Set Your Selling Price (₹) *
                </label>
                <input
                  type="number" min="1"
                  style={{ fontSize: '1.6rem', fontWeight: 800, padding: '0.6rem 1rem', borderRadius: 'var(--radius-md)', border: '2px solid #10B981', width: '100%', outline: 'none', color: '#166534' }}
                  placeholder="₹ 0"
                  value={editPrice}
                  onChange={e => setEditPrice(e.target.value)}
                />
                {editPrice && Number(editPrice) > 0 && (
                  <p style={{ margin: '0.4rem 0 0', fontSize: '0.82rem', color: '#166534' }}>
                    Buyers will see: <strong>₹{Number(editPrice).toLocaleString('en-IN')}</strong> per piece &nbsp;·&nbsp; Min order: {editMoq} pcs
                  </p>
                )}
              </div>

              {/* ── Product Variations (Optional) ── */}
              <div style={{
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
                marginBottom: '1rem',
              }}>
                <button
                  type="button"
                  onClick={() => setShowVariations(v => !v)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: 0,
                    textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Layers size={18} color="var(--color-primary)" />
                    <div>
                      <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Add Sizes / Colours / Types</span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginLeft: '0.5rem' }}>
                        (Optional — optional simple options)
                      </span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    {variations.length > 0 && (
                      <span style={{
                        background: 'var(--color-primary-subtle, #F5F3FF)',
                        color: 'var(--color-primary)',
                        padding: '0.15rem 0.55rem',
                        borderRadius: 999,
                        fontSize: '0.75rem',
                        fontWeight: 700,
                      }}>
                        {variations.length} added
                      </span>
                    )}
                    {showVariations ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </button>

                {showVariations && (
                  <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--color-border)' }}>
                    <p style={{ margin: '0 0 0.75rem', fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                      Tap chips below to add standard sizes, colors, or materials. No typing needed!
                    </p>
                    <VariationPicker
                      basePrice={Number(editPrice) || 0}
                      variations={variations}
                      onChange={setVariations}
                    />
                  </div>
                )}
              </div>

              {/* Advanced toggle */}
              <button type="button"
                onClick={() => setShowAdvanced(v => !v)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '1rem', padding: 0 }}
              >
                {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                {showAdvanced ? 'Hide' : 'Edit'} title, description, quantity & location
              </button>

              {showAdvanced && (
                <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1rem' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Product Title</label>
                    <input className="form-control" value={editTitle} onChange={e => setEditTitle(e.target.value)} />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Description</label>
                    <textarea className="form-control" rows={3} value={editDesc} onChange={e => setEditDesc(e.target.value)} style={{ resize: 'vertical' }} />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label">Quantity</label>
                      <input type="number" className="form-control" min="1" value={editQty} onChange={e => setEditQty(e.target.value)} />
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label">Min Order (MOQ)</label>
                      <input type="number" className="form-control" min="1" value={editMoq} onChange={e => setEditMoq(e.target.value)} />
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label">Location</label>
                      <input className="form-control" value={editLoc} onChange={e => setEditLoc(e.target.value)} />
                    </div>
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Keywords (comma separated)</label>
                    <input className="form-control" placeholder="handmade, bamboo, eco-friendly" value={editKw} onChange={e => setEditKw(e.target.value)} />
                  </div>
                </div>
              )}

              {/* PUBLISH BUTTON */}
              <button type="button"
                onClick={handlePublish}
                disabled={busy || !editPrice || Number(editPrice) <= 0}
                style={{
                  width: '100%', fontSize: '1.1rem', padding: '1rem',
                  background: '#10B981', border: 'none', borderRadius: 'var(--radius-md)',
                  color: '#fff', fontWeight: 700, cursor: busy ? 'wait' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                  opacity: (!editPrice || Number(editPrice) <= 0) ? 0.5 : 1,
                  transition: 'opacity 0.2s',
                }}
              >
                {busy
                  ? <><Loader2 size={20} className="spin" /><span>Publishing…</span></>
                  : <><CheckCircle2 size={22} /><span>Looks Good — Publish to B2B Buyers ✅</span></>}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════
           STEP 3 — PUBLISHED / LIVE
      ══════════════════════════════════════════════════════════ */}
      {step === 3 && workflow && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

          {/* Big success banner */}
          <div style={{ background: 'linear-gradient(135deg,#10B981 0%,#059669 100%)', borderRadius: 'var(--radius-lg)', padding: '2.5rem 2rem', textAlign: 'center', color: '#fff' }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🎉</div>
            <h2 style={{ fontSize: '1.8rem', margin: '0 0 0.5rem', color: '#fff' }}>Your Product is LIVE!</h2>
            <p style={{ margin: '0 0 1.25rem', opacity: 0.9 }}>
              <strong>{workflow.catalog?.product_title || workflow.product_name}</strong> is now visible to verified B2B buyers.
            </p>
            <div style={{ display: 'inline-flex', gap: '2rem', background: 'rgba(255,255,255,0.15)', borderRadius: 'var(--radius-md)', padding: '0.75rem 1.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{matches.length}</div>
                <div style={{ fontSize: '0.75rem', opacity: 0.85 }}>Buyer Matches</div>
              </div>
              {workflow.pricing?.suggested_selling_price && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>₹{workflow.pricing.suggested_selling_price.toLocaleString('en-IN')}</div>
                  <div style={{ fontSize: '0.75rem', opacity: 0.85 }}>Listed Price</div>
                </div>
              )}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>B2B</div>
                <div style={{ fontSize: '0.75rem', opacity: 0.85 }}>Market Active</div>
              </div>
            </div>
          </div>

          {/* Product summary card */}
          <div className="card" style={{ padding: '1.25rem', display: 'flex', gap: '1rem', alignItems: 'flex-start', flexWrap: 'wrap' }}>
            {workflow.images?.[0] && (
              <img src={`${API_BASE}${workflow.images[0].file_url}`} alt="product"
                style={{ width: 100, height: 100, objectFit: 'contain', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', background: '#fff', flexShrink: 0 }} />
            )}
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: '0 0 0.25rem', fontSize: '1.1rem' }}>{workflow.catalog?.product_title || workflow.product_name}</h3>
              <p style={{ margin: '0 0 0.5rem', fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                {workflow.catalog?.product_details?.material && <><strong>Material:</strong> {workflow.catalog.product_details.material} &nbsp;·&nbsp;</>}
                {workflow.catalog?.product_details?.craft_type && <>{workflow.catalog.product_details.craft_type}</>}
              </p>
              {workflow.catalog?.description && (
                <p style={{ margin: '0 0 0.5rem', fontSize: '0.83rem', lineHeight: 1.6, WebkitLineClamp: 3, overflow: 'hidden', display: '-webkit-box', WebkitBoxOrient: 'vertical' }}>
                  {workflow.catalog.description}
                </p>
              )}
              {(workflow.catalog?.keywords || []).length > 0 && (
                <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                  {(workflow.catalog!.keywords || []).slice(0, 6).map(k => (
                    <span key={k} style={{ background: 'var(--color-bg-subtle)', border: '1px solid var(--color-border)', borderRadius: 999, padding: '0.15rem 0.55rem', fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
                      {k}
                    </span>
                  ))}
                </div>
              )}

              {/* Variations on Step 3 */}
              {(workflow.variations || variations).length > 0 && (
                <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--color-border)' }}>
                  <p style={{ margin: '0 0 0.35rem', fontSize: '0.78rem', fontWeight: 700, color: 'var(--color-text-muted)' }}>
                    Available Options / Variations:
                  </p>
                  <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                    {(workflow.variations || variations).map(v => (
                      <span key={v.variation_id} style={{
                        display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
                        background: 'var(--color-primary-subtle, #F5F3FF)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '0.2rem 0.55rem',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: 'var(--color-primary)',
                      }}>
                        <span>{v.emoji || '🔖'}</span>
                        <span>{v.label}</span>
                        {v.price_adjustment !== 0 && (
                          <span style={{ color: v.price_adjustment > 0 ? '#059669' : '#DC2626' }}>
                            ({v.price_adjustment > 0 ? '+' : ''}₹{v.price_adjustment})
                          </span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Buyer matches */}
          <div className="card" style={{ padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Users size={18} color="var(--color-primary)" /> B2B Buyer Matches
            </h3>
            {matches.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                {matches.slice(0, 5).map(m => (
                  <div key={m.match_id} style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', padding: '0.75rem', background: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                    <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, flexShrink: 0 }}>
                      {m.buyer_name?.charAt(0)?.toUpperCase() || 'B'}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ margin: '0 0 0.1rem', fontWeight: 700, fontSize: '0.9rem' }}>{m.buyer_name || 'B2B Buyer'}</p>
                      <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--color-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        Match category: {m.match_category}
                      </p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', flexShrink: 0 }}>
                      <Star size={14} fill="#F59E0B" color="#F59E0B" />
                      <span style={{ fontWeight: 800, fontSize: '0.95rem' }}>{m.match_score}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.88rem', textAlign: 'center', margin: 0 }}>
                Buyers matching your craft will appear here as they post requirements.
              </p>
            )}
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => onNavigate('artisan-dashboard')}>
              <Package size={16} /><span>Go to My Studio</span>
            </button>
            <button className="btn btn-outline" style={{ flex: 1 }} onClick={reset}>
              <Sparkles size={16} /><span>List Another Product</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
