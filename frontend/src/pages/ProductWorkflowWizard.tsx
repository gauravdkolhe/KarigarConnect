import React, { useEffect, useState } from 'react';
import { api, API_BASE } from '../services/api';
import type { ProductMatch, WorkflowState } from '../types';
import { VoiceInputButton } from '../components/VoiceInputButton';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Package,
  Sparkles,
  Star,
  Upload,
  Users,
  Wand2,
  Zap,
} from 'lucide-react';

interface ProductWorkflowWizardProps {
  productId?: string;
  initialStep?: number;
  onNavigate: (view: string, data?: any) => void;
}

// ─── Step indicator ───────────────────────────────────────────────────────────
const STEPS = [
  { num: 1, label: 'Photo', emoji: '📸' },
  { num: 2, label: 'Describe', emoji: '🎙️' },
  { num: 3, label: 'Live on Market', emoji: '✅' },
];

const IMAGE_STYLES = [
  {
    id: 'studio_white',
    name: 'Studio White',
    dot: '#FFFFFF',
    dotBorder: '#CBD5E1',
    desc: 'Crisp white background — standard for Amazon & Etsy',
  },
  {
    id: 'warm_heritage',
    name: 'Warm Heritage',
    dot: '#FAF8F5',
    dotBorder: '#D6D3D1',
    desc: 'Warm ivory with rich saturation — best for wood, brass & clay',
  },
  {
    id: 'modern_minimalist',
    name: 'Modern Minimalist',
    dot: '#F3F4F6',
    dotBorder: '#9CA3AF',
    desc: 'Neutral gray studio with drop shadow — modern gallery look',
  },
  {
    id: 'original',
    name: 'Keep Original',
    dot: 'linear-gradient(135deg,#fde68a,#a7f3d0)',
    dotBorder: '#6EE7B7',
    desc: 'Preserve your raw photo exactly as taken — no edits',
  },
];

export const ProductWorkflowWizard: React.FC<ProductWorkflowWizardProps> = ({
  productId: initialProductId,
  onNavigate,
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [matches, setMatches] = useState<ProductMatch[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // ── Step 1: Photo ───────────────────────────────────────────────────────────
  const [productName, setProductName] = useState('');
  const [category, setCategory] = useState('Home Decor & Storage');
  const [initialMaterial, setInitialMaterial] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('studio_white');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageProcessing, setImageProcessing] = useState(false);

  // ── Step 2: Describe ────────────────────────────────────────────────────────
  const [spokenText, setSpokenText] = useState('');
  const [language, setLanguage] = useState('Hindi');
  const [estimatedCost, setEstimatedCost] = useState<string>('');
  const [desiredPrice, setDesiredPrice] = useState<string>('');
  const [aiGenerating, setAiGenerating] = useState(false);

  // AI-generated / editable result
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editKeywords, setEditKeywords] = useState('');
  const [editMaterial, setEditMaterial] = useState('');
  const [editCraftType, setEditCraftType] = useState('');
  const [editPrice, setEditPrice] = useState<string>('');
  const [editQty, setEditQty] = useState<string>('20');
  const [editMoq, setEditMoq] = useState<string>('5');
  const [editLocation, setEditLocation] = useState('India');
  const [aiResultReady, setAiResultReady] = useState(false);

  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (initialProductId) loadExistingProduct(initialProductId);
  }, [initialProductId]);

  const loadExistingProduct = async (pid: string) => {
    setIsLoading(true);
    try {
      const state = await api.getProductWorkflow(pid);
      setWorkflow(state);
      setProductName(state.product_name);
      if (state.workflow_status === 'published') {
        setCurrentStep(3);
        loadMatches(state.product_id);
      } else if (state.catalog) {
        prefillFromCatalog(state);
        setAiResultReady(true);
        setCurrentStep(2);
      } else if (state.images.length > 0) {
        setCurrentStep(2);
      }
    } catch (e: any) {
      setError(e.message || 'Failed to load product.');
    } finally {
      setIsLoading(false);
    }
  };

  const prefillFromCatalog = (state: WorkflowState) => {
    if (!state.catalog) return;
    setEditTitle(state.catalog.product_title || state.product_name);
    setEditDescription(state.catalog.description || '');
    setEditKeywords(state.catalog.keywords?.join(', ') || '');
    setEditMaterial(state.catalog.product_details?.material || '');
    setEditCraftType(state.catalog.product_details?.craft_type || '');
    if (state.pricing?.suggested_selling_price) {
      setEditPrice(String(state.pricing.suggested_selling_price));
    }
    if (state.inventory) {
      setEditQty(String(state.inventory.available_quantity));
      setEditMoq(String(state.inventory.minimum_order_quantity));
      setEditLocation(state.inventory.location);
    }
  };

  const showError = (msg: string) => {
    setError(msg);
    setSuccessMsg(null);
  };
  const showSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setError(null);
  };

  const loadMatches = async (pid: string) => {
    try {
      const res = await api.getProductMatches(pid, 20);
      setMatches(res.matches || []);
    } catch {
      // quiet
    }
  };

  // ── STEP 1 HANDLERS ─────────────────────────────────────────────────────────

  const handleFileSelect = (file: File) => {
    setUploadFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleStep1Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName.trim()) { showError('Please enter a product name.'); return; }

    setIsLoading(true);
    setError(null);
    try {
      // 1a. Create draft
      const draft = await api.createProductDraft({
        product_name: productName,
        category,
        initial_material: initialMaterial || 'Handcraft',
        initial_craft_type: 'Traditional',
      });
      setWorkflow(draft);

      // 1b. If photo selected → enhance
      if (uploadFile) {
        setImageProcessing(true);
        await api.uploadProductImage(draft.product_id, uploadFile, selectedStyle);
        const updated = await api.getProductWorkflow(draft.product_id);
        setWorkflow(updated);
        setImageProcessing(false);
        showSuccess('✨ Photo processed! Now describe your craft.');
      } else {
        showSuccess('Draft created! Now describe your craft.');
      }
      setCurrentStep(2);
    } catch (err: any) {
      showError(err.message || 'Failed to create product. Try again.');
    } finally {
      setIsLoading(false);
      setImageProcessing(false);
    }
  };

  // ── STEP 2 HANDLERS ─────────────────────────────────────────────────────────

  const handleQuickAssist = async () => {
    if (!workflow) return;
    if (!spokenText.trim()) { showError('Please describe your craft first (speak or type).'); return; }
    setAiGenerating(true);
    setError(null);
    try {
      const res = await api.quickAssist(workflow.product_id, {
        spoken_text: spokenText,
        language,
        estimated_cost: estimatedCost ? Number(estimatedCost) : undefined,
        desired_price: desiredPrice ? Number(desiredPrice) : undefined,
      });
      setWorkflow(res);
      prefillFromCatalog(res);
      setAiResultReady(true);
      showSuccess('🤖 AI generated description & price — review and edit below!');
    } catch (err: any) {
      showError(err.message || 'AI generation failed. Please try again.');
    } finally {
      setAiGenerating(false);
    }
  };

  const handlePublish = async () => {
    if (!workflow) return;
    if (!editTitle.trim()) { showError('Product title is required.'); return; }
    if (!editPrice || Number(editPrice) <= 0) { showError('Please set a valid price.'); return; }

    setIsLoading(true);
    setError(null);
    try {
      const res = await api.oneClickApprove(workflow.product_id, {
        product_title: editTitle,
        description: editDescription,
        keywords: editKeywords.split(',').map((k) => k.trim()).filter(Boolean),
        material: editMaterial || initialMaterial || 'Handcraft',
        craft_type: editCraftType,
        suggested_price: Number(editPrice),
        available_quantity: Number(editQty) || 20,
        minimum_order_quantity: Number(editMoq) || 5,
        location: editLocation || 'India',
      });
      setWorkflow(res);
      await loadMatches(res.product_id);
      showSuccess('🎉 Your product is live on the B2B marketplace!');
      setCurrentStep(3);
    } catch (err: any) {
      showError(err.message || 'Publishing failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto', paddingBottom: '3rem' }}>

      {/* Back nav */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <button className="btn btn-outline btn-sm" onClick={() => onNavigate('artisan-dashboard')}>
          <ArrowLeft size={16} />
          <span>Back to Studio</span>
        </button>
        {workflow && (
          <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
            ID: <strong>{workflow.product_id.slice(-8).toUpperCase()}</strong>
          </span>
        )}
      </div>

      {/* ── Stepper ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '2rem', gap: 0 }}>
        {STEPS.map((s, idx) => {
          const isActive = currentStep === s.num;
          const isDone = currentStep > s.num;
          return (
            <React.Fragment key={s.num}>
              <div
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem', cursor: isDone ? 'pointer' : 'default' }}
                onClick={() => { if (isDone) setCurrentStep(s.num); }}
              >
                <div style={{
                  width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: isDone ? '1.1rem' : '1.3rem',
                  fontWeight: 700,
                  background: isDone ? 'var(--color-success)' : isActive ? 'var(--color-primary)' : 'var(--color-bg-subtle)',
                  color: isDone || isActive ? '#fff' : 'var(--color-text-muted)',
                  border: isActive ? '3px solid var(--color-primary)' : isDone ? '3px solid var(--color-success)' : '2px solid var(--color-border)',
                  boxShadow: isActive ? '0 0 0 4px rgba(124,58,237,0.15)' : 'none',
                  transition: 'all 0.25s ease',
                }}>
                  {isDone ? <CheckCircle2 size={22} /> : s.emoji}
                </div>
                <span style={{ fontSize: '0.75rem', fontWeight: isActive ? 700 : 500, color: isActive ? 'var(--color-primary)' : isDone ? 'var(--color-success)' : 'var(--color-text-muted)' }}>
                  {s.label}
                </span>
              </div>
              {idx < STEPS.length - 1 && (
                <div style={{ flex: 1, height: '3px', background: currentStep > s.num ? 'var(--color-success)' : 'var(--color-border)', margin: '0 0.5rem', marginBottom: '1.1rem', borderRadius: '2px', transition: 'background 0.4s ease', maxWidth: '120px' }} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* ── Alerts ── */}
      {error && (
        <div style={{ background: 'var(--color-danger-bg)', color: 'var(--color-danger)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={16} /> <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div style={{ background: 'var(--color-success-bg)', color: 'var(--color-success)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={16} /> <span>{successMsg}</span>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          STEP 1 — PHOTO
      ════════════════════════════════════════════════════════ */}
      {currentStep === 1 && (
        <form onSubmit={handleStep1Submit}>
          <div className="card" style={{ padding: '2rem' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.6rem', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>📸</span> Step 1: Upload Your Craft Photo
              </h2>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                Share a photo of your creation. Our AI will make it look professional — or keep it raw if you prefer.
              </p>
            </div>

            {/* Product Name */}
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label className="form-label" style={{ margin: 0 }}>Product Name *</label>
                <VoiceInputButton
                  onTranscript={(t) => setProductName((prev) => (prev ? `${prev} ${t}` : t))}
                  placeholder="Listening for product name..."
                />
              </div>
              <input
                type="text" className="form-control" required
                placeholder="e.g. Handwoven Bamboo Storage Basket"
                value={productName} onChange={(e) => setProductName(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div className="form-group">
                <label className="form-label">Category</label>
                <input type="text" className="form-control" placeholder="e.g. Home Decor & Storage"
                  value={category} onChange={(e) => setCategory(e.target.value)} />
              </div>
              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <label className="form-label" style={{ margin: 0 }}>Material Used</label>
                  <VoiceInputButton
                    onTranscript={(t) => setInitialMaterial((prev) => (prev ? `${prev} ${t}` : t))}
                    placeholder="Listening..."
                  />
                </div>
                <input type="text" className="form-control" placeholder="e.g. Bamboo, Clay, Silk"
                  value={initialMaterial} onChange={(e) => setInitialMaterial(e.target.value)} />
              </div>
            </div>

            {/* Photo Upload */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Upload size={16} color="var(--color-primary)" />
                <span>Upload Craft Photo <span style={{ fontWeight: 400, color: 'var(--color-text-muted)' }}>(optional — you can add later)</span></span>
              </label>

              {/* Drag drop / click area */}
              <label htmlFor="photo-upload" style={{
                display: 'block', border: '2px dashed var(--color-border)', borderRadius: 'var(--radius-lg)',
                padding: imagePreview ? '0' : '2.5rem 1.5rem', textAlign: 'center',
                background: 'var(--color-bg-subtle)', cursor: 'pointer', overflow: 'hidden',
                transition: 'border-color 0.2s',
              }}>
                {imagePreview ? (
                  <img src={imagePreview} alt="Preview" style={{ width: '100%', maxHeight: '300px', objectFit: 'contain', display: 'block' }} />
                ) : (
                  <>
                    <Upload size={32} color="var(--color-primary)" style={{ marginBottom: '0.5rem' }} />
                    <p style={{ margin: '0 0 0.25rem', fontWeight: 600 }}>Click to choose a photo</p>
                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>JPG, PNG or WebP — max 10 MB</p>
                  </>
                )}
              </label>
              <input id="photo-upload" type="file" accept="image/jpeg,image/png,image/webp"
                style={{ display: 'none' }}
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }}
              />
              {uploadFile && (
                <p style={{ marginTop: '0.5rem', fontSize: '0.82rem', color: 'var(--color-primary)', fontWeight: 600 }}>
                  Selected: {uploadFile.name} ({(uploadFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            {/* Style selector — shown only when photo selected */}
            {uploadFile && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label className="form-label">Choose Photo Style</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
                  {IMAGE_STYLES.map((s) => (
                    <div
                      key={s.id}
                      onClick={() => setSelectedStyle(s.id)}
                      style={{
                        border: selectedStyle === s.id ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)', padding: '0.85rem',
                        cursor: 'pointer',
                        background: selectedStyle === s.id ? 'var(--color-primary-subtle, #F5F3FF)' : 'var(--color-bg)',
                        transition: 'all 0.18s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                        <span style={{ width: '16px', height: '16px', borderRadius: '50%', background: s.dot, border: `1px solid ${s.dotBorder}`, flexShrink: 0, display: 'inline-block' }} />
                        <span style={{ fontWeight: 700, fontSize: '0.88rem' }}>{s.name}</span>
                      </div>
                      <p style={{ fontSize: '0.76rem', color: 'var(--color-text-muted)', margin: 0 }}>{s.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button type="submit" className="btn btn-primary" style={{ fontSize: '1rem', padding: '0.75rem 2rem' }} disabled={isLoading || imageProcessing}>
              {(isLoading || imageProcessing) ? (
                <><Loader2 size={18} className="spin" /><span>{imageProcessing ? 'Enhancing photo...' : 'Creating...'}</span></>
              ) : (
                <><span>{uploadFile ? 'Use This Photo & Continue' : 'Continue Without Photo'}</span><ArrowRight size={18} /></>
              )}
            </button>
          </div>
        </form>
      )}

      {/* ════════════════════════════════════════════════════════
          STEP 2 — DESCRIBE
      ════════════════════════════════════════════════════════ */}
      {currentStep === 2 && workflow && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* ── Uploaded image preview ── */}
          {workflow.images && workflow.images.length > 0 && (
            <div className="card" style={{ padding: '1rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              {workflow.images.slice(0, 3).map((img) => (
                <div key={img.image_id} style={{ border: '2px solid var(--color-success)', borderRadius: 'var(--radius-md)', overflow: 'hidden', width: '100px', height: '100px', background: '#fff', flexShrink: 0 }}>
                  <img src={`${API_BASE}${img.file_url}`} alt="Craft" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                </div>
              ))}
              <div>
                <p style={{ margin: '0 0 0.25rem', fontWeight: 700, color: 'var(--color-success)', fontSize: '0.88rem' }}>✓ Photo Ready</p>
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{workflow.images.length} image(s) processed — 1200×1200</p>
              </div>
            </div>
          )}

          {/* ── Voice / Text input ── */}
          <div className="card" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.6rem', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>🎙️</span> Step 2: Describe Your Craft
            </h2>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Speak or type in your local language. AI will write the product description and suggest a fair price.
            </p>

            {/* Language + Voice row */}
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', marginBottom: '1rem', flexWrap: 'wrap' }}>
              <div className="form-group" style={{ flex: '0 0 180px', marginBottom: 0 }}>
                <label className="form-label">Language</label>
                <select className="form-control" value={language} onChange={(e) => setLanguage(e.target.value)}>
                  {['Hindi', 'Marathi', 'Bengali', 'Tamil', 'Telugu', 'Kannada', 'Gujarati', 'Punjabi', 'Odia', 'Assamese', 'English'].map((l) => (
                    <option key={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <label className="form-label" style={{ margin: 0 }}>Tap microphone & speak</label>
                <VoiceInputButton
                  onTranscript={(t) => setSpokenText((prev) => (prev ? `${prev} ${t}` : t))}
                  placeholder={`Listening in ${language}...`}
                />
              </div>
            </div>

            {/* Large mic hero button */}
            <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
              <VoiceInputButton
                onTranscript={(t) => setSpokenText((prev) => (prev ? `${prev} ${t}` : t))}
                placeholder={`Speak in ${language}...`}
                large
              />
              <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
                Tap the mic and describe your product in {language}
              </p>
            </div>

            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="form-label">Description (spoken or typed)</label>
              <textarea
                className="form-control"
                rows={4}
                placeholder={`Type or speak — describe your craft in ${language} or any language. E.g. "यह बाँस की टोकरी हाथ से बुनी गई है..."`}
                value={spokenText}
                onChange={(e) => setSpokenText(e.target.value)}
                style={{ resize: 'vertical' }}
              />
            </div>

            {/* Cost hints */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Material cost (₹) <span style={{ fontWeight: 400, color: 'var(--color-text-muted)' }}>optional</span></label>
                <input type="number" className="form-control" placeholder="e.g. 200"
                  value={estimatedCost} onChange={(e) => setEstimatedCost(e.target.value)} min="0" />
                <small style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>How much did materials cost you?</small>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Your desired price (₹) <span style={{ fontWeight: 400, color: 'var(--color-text-muted)' }}>optional</span></label>
                <input type="number" className="form-control" placeholder="e.g. 850"
                  value={desiredPrice} onChange={(e) => setDesiredPrice(e.target.value)} min="0" />
                <small style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>What price do you want to sell at?</small>
              </div>
            </div>

            <button
              type="button" className="btn btn-primary"
              style={{ width: '100%', fontSize: '1rem', padding: '0.85rem' }}
              onClick={handleQuickAssist}
              disabled={aiGenerating || !spokenText.trim()}
            >
              {aiGenerating ? (
                <><Loader2 size={18} className="spin" /><span>AI is generating description & price...</span></>
              ) : (
                <><Wand2 size={18} /><span>Generate AI Description & Price</span></>
              )}
            </button>
          </div>

          {/* ── AI Result — editable ── */}
          {aiResultReady && (
            <div className="card" style={{ padding: '2rem', border: '2px solid var(--color-primary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                <Sparkles size={22} color="var(--color-primary)" />
                <h3 style={{ margin: 0, fontSize: '1.2rem' }}>AI-Generated Details — Review & Edit</h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group" style={{ gridColumn: '1 / -1', marginBottom: 0 }}>
                  <label className="form-label">Product Title *</label>
                  <input type="text" className="form-control" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} placeholder="Product title" />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Material</label>
                  <input type="text" className="form-control" value={editMaterial} onChange={(e) => setEditMaterial(e.target.value)} placeholder="e.g. Bamboo" />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Craft Technique</label>
                  <input type="text" className="form-control" value={editCraftType} onChange={(e) => setEditCraftType(e.target.value)} placeholder="e.g. Handwoven" />
                </div>
                <div className="form-group" style={{ gridColumn: '1 / -1', marginBottom: 0 }}>
                  <label className="form-label">Description</label>
                  <textarea className="form-control" rows={4} value={editDescription} onChange={(e) => setEditDescription(e.target.value)} style={{ resize: 'vertical' }} />
                </div>
                <div className="form-group" style={{ gridColumn: '1 / -1', marginBottom: 0 }}>
                  <label className="form-label">Keywords (comma-separated)</label>
                  <input type="text" className="form-control" value={editKeywords} onChange={(e) => setEditKeywords(e.target.value)} placeholder="handmade, bamboo, eco-friendly" />
                </div>
              </div>

              {/* Price & Inventory row */}
              <div style={{ background: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)', padding: '1rem', marginBottom: '1.25rem' }}>
                <p style={{ margin: '0 0 0.75rem', fontWeight: 700, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Zap size={16} color="var(--color-primary)" /> Pricing & Inventory
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Selling Price (₹) *</label>
                    <input type="number" className="form-control" value={editPrice} onChange={(e) => setEditPrice(e.target.value)} placeholder="₹" min="1" style={{ fontWeight: 700, fontSize: '1.1rem' }} />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Available Qty</label>
                    <input type="number" className="form-control" value={editQty} onChange={(e) => setEditQty(e.target.value)} min="1" />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Min Order (MOQ)</label>
                    <input type="number" className="form-control" value={editMoq} onChange={(e) => setEditMoq(e.target.value)} min="1" />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Location</label>
                    <input type="text" className="form-control" value={editLocation} onChange={(e) => setEditLocation(e.target.value)} placeholder="State, India" />
                  </div>
                </div>
              </div>

              <button
                type="button" className="btn btn-success"
                style={{ width: '100%', fontSize: '1.05rem', padding: '0.9rem', background: 'var(--color-success)', border: 'none' }}
                onClick={handlePublish}
                disabled={isLoading}
              >
                {isLoading ? (
                  <><Loader2 size={18} className="spin" /><span>Publishing to B2B Market...</span></>
                ) : (
                  <><CheckCircle2 size={20} /><span>Looks Good — Publish to Buyers ✅</span></>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          STEP 3 — LIVE ON MARKET
      ════════════════════════════════════════════════════════ */}
      {currentStep === 3 && workflow && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Success banner */}
          <div style={{
            background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
            borderRadius: 'var(--radius-lg)', padding: '2.5rem 2rem', textAlign: 'center', color: '#fff',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🎉</div>
            <h2 style={{ fontSize: '1.8rem', margin: '0 0 0.5rem', color: '#fff' }}>Your product is LIVE!</h2>
            <p style={{ margin: '0 0 1rem', opacity: 0.9, fontSize: '1rem' }}>
              <strong>{workflow.product_name}</strong> is now visible to verified B2B buyers on KarigarConnect.
            </p>
            <div style={{ display: 'inline-flex', gap: '1.5rem', background: 'rgba(255,255,255,0.15)', borderRadius: 'var(--radius-md)', padding: '0.75rem 1.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{matches.length}</div>
                <div style={{ fontSize: '0.78rem', opacity: 0.85 }}>Buyer Matches</div>
              </div>
              {workflow.pricing?.suggested_selling_price && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>₹{workflow.pricing.suggested_selling_price}</div>
                  <div style={{ fontSize: '0.78rem', opacity: 0.85 }}>Listed Price</div>
                </div>
              )}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>B2B</div>
                <div style={{ fontSize: '0.78rem', opacity: 0.85 }}>Market Linked</div>
              </div>
            </div>
          </div>

          {/* Product card */}
          <div className="card" style={{ padding: '1.5rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
            {workflow.images && workflow.images.length > 0 && (
              <img
                src={`${API_BASE}${workflow.images[0].file_url}`}
                alt={workflow.product_name}
                style={{ width: '120px', height: '120px', objectFit: 'contain', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', background: '#fff', flexShrink: 0 }}
              />
            )}
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: '0 0 0.25rem', fontSize: '1.15rem' }}>{workflow.catalog?.product_title || workflow.product_name}</h3>
              {workflow.catalog?.product_details?.material && (
                <p style={{ margin: '0 0 0.5rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                  Material: <strong>{workflow.catalog.product_details.material}</strong>
                  {workflow.catalog.product_details.craft_type && ` · ${workflow.catalog.product_details.craft_type}`}
                </p>
              )}
              {workflow.catalog?.description && (
                <p style={{ margin: '0 0 0.75rem', fontSize: '0.85rem', color: 'var(--color-text)', lineHeight: 1.6, WebkitLineClamp: 3, overflow: 'hidden', display: '-webkit-box', WebkitBoxOrient: 'vertical' }}>
                  {workflow.catalog.description}
                </p>
              )}
              {workflow.catalog?.keywords && workflow.catalog.keywords.length > 0 && (
                <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                  {workflow.catalog.keywords.slice(0, 5).map((kw) => (
                    <span key={kw} style={{ background: 'var(--color-bg-subtle)', border: '1px solid var(--color-border)', borderRadius: '999px', padding: '0.2rem 0.6rem', fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Buyer matches */}
          {matches.length > 0 ? (
            <div className="card" style={{ padding: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Users size={18} color="var(--color-primary)" /> Top B2B Buyer Matches
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {matches.slice(0, 5).map((m) => (
                  <div key={m.match_id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.85rem 1rem', background: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                    <div style={{ flexShrink: 0, width: '44px', height: '44px', borderRadius: '50%', background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: '1.1rem' }}>
                      {m.buyer_name?.charAt(0)?.toUpperCase() || 'B'}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ margin: '0 0 0.1rem', fontWeight: 700, fontSize: '0.9rem' }}>{m.buyer_name || 'Anonymous Buyer'}</p>
                    {m.requirement_id && <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>Req: {m.requirement_id.slice(-8).toUpperCase()}</p>}
                    </div>
                    <div style={{ flexShrink: 0, textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#F59E0B', justifyContent: 'flex-end' }}>
                        <Star size={14} fill="#F59E0B" />
                        <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{m.match_score}%</span>
                      </div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>match</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
              <Users size={32} color="var(--color-text-muted)" style={{ marginBottom: '0.5rem' }} />
              <p style={{ margin: '0 0 0.25rem', fontWeight: 700 }}>Scanning B2B Buyer Network...</p>
              <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Buyers matching your craft will appear here as they post requirements.</p>
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => onNavigate('artisan-dashboard')}>
              <Package size={16} /> <span>View My Studio</span>
            </button>
            <button className="btn btn-outline" style={{ flex: 1 }} onClick={() => {
              setCurrentStep(1); setWorkflow(null); setProductName(''); setInitialMaterial('');
              setUploadFile(null); setImagePreview(null); setSpokenText(''); setAiResultReady(false);
              setEditTitle(''); setEditDescription(''); setEditKeywords(''); setEditPrice('');
              setError(null); setSuccessMsg(null); setMatches([]);
            }}>
              <Sparkles size={16} /> <span>List Another Product</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
