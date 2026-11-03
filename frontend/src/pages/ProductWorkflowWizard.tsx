import React, { useEffect, useState } from 'react';
import { api, API_BASE } from '../services/api';
import type { ProductMatch, WorkflowState } from '../types';
import { VoiceInputButton } from '../components/VoiceInputButton';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Calculator,
  CheckCircle2,
  Compass,
  Loader2,
  Palette,
  Send,
  Sparkles,
  Upload,
  Wand2,
} from 'lucide-react';

interface ProductWorkflowWizardProps {
  productId?: string;
  initialStep?: number;
  onNavigate: (view: string, data?: any) => void;
}

export const ProductWorkflowWizard: React.FC<ProductWorkflowWizardProps> = ({
  productId: initialProductId,
  initialStep,
  onNavigate,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(initialStep || 1);
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [matches, setMatches] = useState<ProductMatch[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Step 1: Draft fields
  const [productName, setProductName] = useState('');
  const [category, setCategory] = useState('Home Decor & Storage');
  const [initialMaterial, setInitialMaterial] = useState('Assam Bamboo');
  const [initialCraftType, setInitialCraftType] = useState('Handwoven Lattice');

  // Step 2: Image upload & Styles
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [imageProcessing, setImageProcessing] = useState(false);
  const [selectedStyle, setSelectedStyle] = useState<string>('studio_white');
  const [isRestyling, setIsRestyling] = useState<boolean>(false);

  // Step 3: Catalog approval & AI generation
  const [aiGeneratingCatalog, setAiGeneratingCatalog] = useState<boolean>(false);
  const [catalogTitle, setCatalogTitle] = useState('');
  const [catalogDescription, setCatalogDescription] = useState('');
  const [catalogKeywords, setCatalogKeywords] = useState('');
  const [catalogMaterial, setCatalogMaterial] = useState('');
  const [catalogCraftType, setCatalogCraftType] = useState('');
  const [catalogColor, setCatalogColor] = useState('Natural Amber');
  const [catalogPurpose, setCatalogPurpose] = useState('Storage');

  // Step 4: Pricing fields
  const [materialCost, setMaterialCost] = useState<number>(300);
  const [laborCost, setLaborCost] = useState<number>(200);
  const [packagingCost, setPackagingCost] = useState<number>(50);
  const [overheadCost, setOverheadCost] = useState<number>(50);
  const [shippingCost, setShippingCost] = useState<number>(50);
  const [targetMargin, setTargetMargin] = useState<number>(25);
  const [marketplaceCommission, setMarketplaceCommission] = useState<number>(10);
  const [pricingStrategy, setPricingStrategy] = useState<'exact' | 'round_nearest_rupee' | 'psychological_99'>('round_nearest_rupee');

  // Step 5: Inventory fields
  const [availableQuantity, setAvailableQuantity] = useState<number>(30);
  const [monthlyCapacity, setMonthlyCapacity] = useState<number>(100);
  const [moq, setMoq] = useState<number>(5);
  const [leadTimeDays, setLeadTimeDays] = useState<number>(14);
  const [workshopLocation, setWorkshopLocation] = useState<string>('Assam, India');

  useEffect(() => {
    if (initialProductId) {
      loadProductWorkflow(initialProductId, initialStep);
    } else if (initialStep) {
      setCurrentStep(initialStep);
    }
  }, [initialProductId, initialStep]);

  const loadProductWorkflow = async (pid: string, targetStep?: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const state = await api.getProductWorkflow(pid);
      setWorkflow(state);

      // Pre-fill steps
      setProductName(state.product_name);
      if (state.catalog) {
        setCatalogTitle(state.catalog.product_title || state.product_name);
        setCatalogDescription(state.catalog.description || '');
        setCatalogKeywords(state.catalog.keywords?.join(', ') || '');
        setCatalogMaterial(state.catalog.product_details?.material || 'Assam Bamboo');
        setCatalogCraftType(state.catalog.product_details?.craft_type || '');
        setCatalogColor(state.catalog.product_details?.color || 'Natural Amber');
        setCatalogPurpose(state.catalog.product_details?.purpose || 'Storage');
      }
      if (state.pricing) {
        setMaterialCost(state.pricing.cost_breakdown?.material_cost || 300);
        setLaborCost(state.pricing.cost_breakdown?.labor_cost || 200);
      }
      if (state.inventory) {
        setAvailableQuantity(state.inventory.available_quantity);
        setMonthlyCapacity(state.inventory.production_capacity_per_month);
        setWorkshopLocation(state.inventory.location);
      }

      // Determine active step if not explicitly set
      if (targetStep) {
        setCurrentStep(targetStep);
      } else if (state.workflow_status === 'published') {
        setCurrentStep(7);
      } else if (state.inventory) {
        setCurrentStep(6);
      } else if (state.pricing) {
        setCurrentStep(5);
      } else if (state.catalog?.description) {
        setCurrentStep(4);
      } else if (state.images.length > 0) {
        setCurrentStep(3);
      } else {
        setCurrentStep(2);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load product workflow.');
    } finally {
      setIsLoading(false);
    }
  };

  // STEP 1: Create draft
  const handleCreateDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.createProductDraft({
        product_name: productName,
        category,
        initial_material: initialMaterial,
        initial_craft_type: initialCraftType,
      });
      setWorkflow(res);
      setSuccessMsg('Product draft created! Now upload craft photos.');
      setCurrentStep(2);
    } catch (err: any) {
      setError(err.message || 'Draft creation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  // STEP 2: Image Enhancement
  const handleUploadImage = async () => {
    if (!workflow || !uploadFile) return;
    setImageProcessing(true);
    setError(null);
    try {
      await api.uploadProductImage(workflow.product_id, uploadFile, selectedStyle);
      const updated = await api.getProductWorkflow(workflow.product_id);
      setWorkflow(updated);
      setSuccessMsg(`Image enhanced with white background & ${selectedStyle === 'studio_white' ? 'Studio Pure White' : selectedStyle === 'warm_heritage' ? 'Warm Heritage' : 'Modern Minimalist'} style!`);
      setCurrentStep(3);
    } catch (err: any) {
      setError(err.message || 'Image enhancement failed.');
    } finally {
      setImageProcessing(false);
    }
  };

  // STEP 2: Re-style existing image
  const handleRestyleImage = async (imageId: string, style: string) => {
    if (!workflow) return;
    setIsRestyling(true);
    setError(null);
    try {
      await api.restyleProductImage(imageId, style);
      const updated = await api.getProductWorkflow(workflow.product_id);
      setWorkflow(updated);
      setSuccessMsg(`Image re-rendered with new style (${style})!`);
    } catch (err: any) {
      setError(err.message || 'Failed to apply new style to image.');
    } finally {
      setIsRestyling(false);
    }
  };

  // STEP 3: Auto-generate with Gemini AI Agent
  const handleAutoGenerateAICatalog = async () => {
    if (!workflow) return;
    setAiGeneratingCatalog(true);
    setError(null);
    try {
      const updated = await api.generateAICatalog(workflow.product_id);
      setWorkflow(updated);
      if (updated.catalog) {
        setCatalogTitle(updated.catalog.product_title || updated.product_name);
        setCatalogDescription(updated.catalog.description || '');
        setCatalogKeywords(updated.catalog.keywords?.join(', ') || '');
        if (updated.catalog.product_details?.material) {
          setCatalogMaterial(updated.catalog.product_details.material);
        }
        if (updated.catalog.product_details?.craft_type) {
          setCatalogCraftType(updated.catalog.product_details.craft_type);
        }
        if (updated.catalog.product_details?.color) {
          setCatalogColor(updated.catalog.product_details.color);
        }
        if (updated.catalog.product_details?.purpose) {
          setCatalogPurpose(updated.catalog.product_details.purpose);
        }
      }
      setSuccessMsg('✨ AI Product Catalog Agent generated commercial title, keywords, and craft description! Review and approve below.');
    } catch (err: any) {
      setError(err.message || 'AI catalog generation failed.');
    } finally {
      setAiGeneratingCatalog(false);
    }
  };

  // STEP 3: Catalog Approval
  const handleCatalogApproval = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workflow) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.approveCatalog(workflow.product_id, {
        product_title: catalogTitle || workflow.product_name,
        description: catalogDescription,
        keywords: catalogKeywords.split(',').map((s) => s.trim()).filter(Boolean),
        material: catalogMaterial || 'Assam Bamboo',
        craft_type: catalogCraftType,
        color: catalogColor,
        purpose: catalogPurpose,
      });
      setWorkflow(res);
      setSuccessMsg('Artisan catalog approved and persisted.');
      setCurrentStep(4);
    } catch (err: any) {
      setError(err.message || 'Catalog save failed.');
    } finally {
      setIsLoading(false);
    }
  };

  // STEP 4: Pricing Calculation
  const handleCalculatePricing = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workflow) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.calculatePricing(workflow.product_id, {
        material_cost: materialCost,
        labor_cost: laborCost,
        packaging_cost: packagingCost,
        overhead_cost: overheadCost,
        shipping_cost: shippingCost,
        target_profit_margin_percent: targetMargin,
        marketplace_commission_percent: marketplaceCommission,
        pricing_strategy: pricingStrategy,
      });
      setWorkflow(res);
      setSuccessMsg(`Price calculated: ₹${res.pricing?.suggested_selling_price}`);
      setCurrentStep(5);
    } catch (err: any) {
      setError(err.message || 'Pricing calculation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  // STEP 5: Inventory Configuration
  const handleSaveInventory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workflow) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.saveInventory(workflow.product_id, {
        available_quantity: availableQuantity,
        production_capacity_per_month: monthlyCapacity,
        minimum_order_quantity: moq,
        production_lead_time_days: leadTimeDays,
        location: workshopLocation,
      });
      setWorkflow(res);
      setSuccessMsg('Artisan operational inventory saved.');
      // Automatically load matches for Step 6
      loadMatches(workflow.product_id);
      setCurrentStep(6);
    } catch (err: any) {
      setError(err.message || 'Inventory configuration failed.');
    } finally {
      setIsLoading(false);
    }
  };

  // STEP 6: Load Market Linkage Matches
  const loadMatches = async (pid: string) => {
    try {
      const res = await api.getProductMatches(pid, 20);
      setMatches(res.matches || []);
    } catch {
      // quiet
    }
  };

  // STEP 7: Publish
  const handlePublish = async () => {
    if (!workflow) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.publishProduct(workflow.product_id);
      setWorkflow(res);
      setSuccessMsg('🎉 Product published successfully to the marketplace!');
      setCurrentStep(7);
    } catch (err: any) {
      setError(err.message || 'Publication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const steps = [
    { num: 1, label: 'Draft' },
    { num: 2, label: 'Image AI' },
    { num: 3, label: 'Catalog' },
    { num: 4, label: 'Pricing' },
    { num: 5, label: 'Inventory' },
    { num: 6, label: 'Matches' },
    { num: 7, label: 'Publish' },
  ];

  return (
    <div style={{ maxWidth: '920px', margin: '0 auto' }}>
      {/* Navigation & Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <button
          className="btn btn-outline btn-sm"
          onClick={() => onNavigate('artisan-dashboard')}
        >
          <ArrowLeft size={16} />
          <span>Back to Studio</span>
        </button>

        {workflow && (
          <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
            Product ID: <strong>{workflow.product_id}</strong>
          </span>
        )}
      </div>

      {/* Stepper Wizard Bar */}
      <div className="stepper">
        {steps.map((s) => {
          const isActive = currentStep === s.num;
          const isDone = currentStep > s.num;
          return (
            <div
              key={s.num}
              className={`step-item ${isActive ? 'active' : ''} ${isDone ? 'completed' : ''}`}
              onClick={() => {
                // allow navigating to completed steps if workflow exists
                if (workflow && s.num <= currentStep) setCurrentStep(s.num);
              }}
              style={{ cursor: workflow ? 'pointer' : 'default' }}
            >
              <div className="step-circle">
                {isDone ? <CheckCircle2 size={18} /> : s.num}
              </div>
              <span className="step-title">{s.label}</span>
            </div>
          );
        })}
      </div>

      {/* Alert Banners */}
      {error && (
        <div
          style={{
            background: 'var(--color-danger-bg)',
            color: 'var(--color-danger)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div
          style={{
            background: 'var(--color-success-bg)',
            color: 'var(--color-success)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <CheckCircle2 size={16} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* WIZARD STEP CONTENTS */}
      <div className="card" style={{ padding: '2rem' }}>
        {/* STEP 1: DRAFT CREATION */}
        {currentStep === 1 && (
          <form onSubmit={handleCreateDraft}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Step 1: Initiate Craft Draft</h2>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                Enter the basic details of your artisanal product to initiate the multi-agent pipeline.
              </p>
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label className="form-label" style={{ margin: 0 }}>Craft / Product Name *</label>
                <VoiceInputButton
                  onTranscript={(text) => setProductName((prev) => (prev ? `${prev} ${text}` : text))}
                  placeholder="Listening to product name..."
                />
              </div>
              <input
                type="text"
                className="form-control"
                required
                placeholder="e.g. Handwoven Bamboo Storage Basket"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Category</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Storage & Organization"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Primary Raw Material</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Assam Bamboo / Cane"
                  value={initialMaterial}
                  onChange={(e) => setInitialMaterial(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label className="form-label" style={{ margin: 0 }}>Crafting Technique</label>
                <VoiceInputButton
                  onTranscript={(text) => setInitialCraftType((prev) => (prev ? `${prev} ${text}` : text))}
                  placeholder="Listening..."
                />
              </div>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Handwoven, Lattice Carving, Natural Dye"
                value={initialCraftType}
                onChange={(e) => setInitialCraftType(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }} disabled={isLoading}>
              <span>Create Draft & Proceed to Image Processing</span>
              <ArrowRight size={16} />
            </button>
          </form>
        )}

        {/* STEP 2: IMAGE ENHANCEMENT */}
        {currentStep === 2 && workflow && (
          <div>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Step 2: AI Image Enhancement Engine</h2>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                Transforms raw workshop photos into marketplace-ready assets with pure white background,
                auto-centered alignment, and high-dynamic contrast.
              </p>
            </div>

            {/* Feature Highlights Banner */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '0.75rem',
                marginBottom: '1.5rem',
                padding: '0.75rem 1rem',
                background: '#F0FDF4',
                border: '1px solid #BBF7D0',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.85rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#166534' }}>
                <CheckCircle2 size={16} />
                <span><strong>White Background</strong> Studio Isolation</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#166534' }}>
                <CheckCircle2 size={16} />
                <span><strong>Auto-Centered</strong> 1200×1200 Framing</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#166534' }}>
                <CheckCircle2 size={16} />
                <span><strong>Optimized</strong> Brightness & Contrast</span>
              </div>
            </div>

            {/* Style Selector with 3 Presets */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Palette size={16} color="var(--color-primary)" />
                <span>Choose Visual Style Preset (3 Options Available)</span>
              </label>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                {/* Style 1: Studio Pure White */}
                <div
                  onClick={() => setSelectedStyle('studio_white')}
                  style={{
                    border: selectedStyle === 'studio_white' ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                    cursor: 'pointer',
                    background: selectedStyle === 'studio_white' ? 'var(--color-primary-subtle, #F5F3FF)' : 'var(--color-bg)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Studio Pure White</span>
                    <span
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: '#FFFFFF',
                        border: '1px solid #CBD5E1',
                        display: 'inline-block',
                      }}
                    />
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 }}>
                    Crisp pure white background with neutral daylight brightness and unsharp masking. Standard for Amazon & Etsy.
                  </p>
                </div>

                {/* Style 2: Warm Heritage & Glow */}
                <div
                  onClick={() => setSelectedStyle('warm_heritage')}
                  style={{
                    border: selectedStyle === 'warm_heritage' ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                    cursor: 'pointer',
                    background: selectedStyle === 'warm_heritage' ? 'var(--color-primary-subtle, #F5F3FF)' : 'var(--color-bg)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Warm Heritage & Glow</span>
                    <span
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: '#FAF8F5',
                        border: '1px solid #D6D3D1',
                        display: 'inline-block',
                      }}
                    />
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 }}>
                    Warm ivory backdrop with rich saturation (+22%) and amber glow to celebrate wood, brass, silk, and clay crafts.
                  </p>
                </div>

                {/* Style 3: Modern Minimalist Gallery */}
                <div
                  onClick={() => setSelectedStyle('modern_minimalist')}
                  style={{
                    border: selectedStyle === 'modern_minimalist' ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                    cursor: 'pointer',
                    background: selectedStyle === 'modern_minimalist' ? 'var(--color-primary-subtle, #F5F3FF)' : 'var(--color-bg)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Modern Minimalist</span>
                    <span
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: '#F3F4F6',
                        border: '1px solid #9CA3AF',
                        display: 'inline-block',
                      }}
                    />
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 }}>
                    Neutral studio gray background with realistic contact drop shadow and high-definition micro-contrast.
                  </p>
                </div>
              </div>
            </div>

            {/* Display existing images if any */}
            {workflow.images && workflow.images.length > 0 && (
              <div style={{ marginBottom: '2rem' }}>
                <label className="form-label">Enhanced Product Assets</label>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  {workflow.images.map((img) => (
                    <div
                      key={img.image_id}
                      style={{
                        position: 'relative',
                        border: '2px solid var(--color-success)',
                        borderRadius: 'var(--radius-md)',
                        overflow: 'hidden',
                        width: '200px',
                        background: '#fff',
                        boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
                      }}
                    >
                      <div style={{ width: '100%', height: '170px', overflow: 'hidden' }}>
                        <img
                          src={`${API_BASE}${img.file_url}`}
                          alt="Enhanced craft"
                          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                        />
                      </div>
                      <div style={{ padding: '0.5rem', background: '#F8FAFC', borderTop: '1px solid #E2E8F0', fontSize: '0.75rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                          <span style={{ fontWeight: 700, color: 'var(--color-success)' }}>✓ STUDIO ENHANCED</span>
                          <span style={{ color: 'var(--color-text-muted)' }}>1200×1200</span>
                        </div>
                        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                          <button
                            type="button"
                            className="btn btn-outline btn-xs"
                            disabled={isRestyling}
                            onClick={() => handleRestyleImage(img.image_id, 'studio_white')}
                            style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem' }}
                          >
                            Pure White
                          </button>
                          <button
                            type="button"
                            className="btn btn-outline btn-xs"
                            disabled={isRestyling}
                            onClick={() => handleRestyleImage(img.image_id, 'warm_heritage')}
                            style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem' }}
                          >
                            Warm Glow
                          </button>
                          <button
                            type="button"
                            className="btn btn-outline btn-xs"
                            disabled={isRestyling}
                            onClick={() => handleRestyleImage(img.image_id, 'modern_minimalist')}
                            style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem' }}
                          >
                            Shadow
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upload Area */}
            <div
              style={{
                border: '2px dashed var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                padding: '2.5rem 1.5rem',
                textAlign: 'center',
                background: 'var(--color-bg-subtle)',
                marginBottom: '1.5rem',
              }}
            >
              <Upload size={36} color="var(--color-primary)" style={{ marginBottom: '0.75rem' }} />
              <h4 style={{ fontSize: '1.1rem', marginBottom: '0.35rem' }}>Select Workshop Photo</h4>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                Upload an unedited craft picture. The engine isolates background, centers the craft, and applies your chosen style.
              </p>

              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                style={{ display: 'none' }}
                id="photo-upload"
              />
              <label htmlFor="photo-upload" className="btn btn-outline btn-sm">
                Choose Image File
              </label>

              {uploadFile && (
                <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-primary)' }}>
                  Selected: {uploadFile.name} ({(uploadFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'space-between' }}>
              <button
                className="btn btn-primary"
                onClick={handleUploadImage}
                disabled={!uploadFile || imageProcessing || isRestyling}
              >
                {imageProcessing ? (
                  <>
                    <Loader2 size={16} className="spin" />
                    <span>Processing & Enhancing Image...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    <span>Enhance with {selectedStyle === 'studio_white' ? 'Pure White' : selectedStyle === 'warm_heritage' ? 'Warm Glow' : 'Modern Shadow'} Style</span>
                  </>
                )}
              </button>

              <button
                className="btn btn-outline"
                onClick={() => setCurrentStep(3)}
              >
                <span>Continue to Catalog &gt;</span>
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: CATALOG APPROVAL */}
        {currentStep === 3 && workflow && (
          <form onSubmit={handleCatalogApproval}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Step 3: Product Catalog Review</h2>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                  Review, edit, and approve your catalog listing. Mandatory artisan approval prevents inaccurate AI generation.
                </p>
              </div>

              {/* AI Auto-generate button */}
              <button
                type="button"
                className="btn btn-outline"
                onClick={handleAutoGenerateAICatalog}
                disabled={aiGeneratingCatalog || isLoading}
                style={{
                  borderColor: 'var(--color-primary)',
                  color: 'var(--color-primary)',
                  background: 'var(--color-primary-subtle, #F5F3FF)',
                }}
              >
                {aiGeneratingCatalog ? (
                  <>
                    <Loader2 size={16} className="spin" />
                    <span>AI Agent Generating...</span>
                  </>
                ) : (
                  <>
                    <Wand2 size={16} />
                    <span>✨ Auto-Draft with Gemini AI Agent</span>
                  </>
                )}
              </button>
            </div>

            <div className="form-group">
              <label className="form-label">Commercial Product Title *</label>
              <input
                type="text"
                className="form-control"
                required
                value={catalogTitle || workflow.product_name}
                onChange={(e) => setCatalogTitle(e.target.value)}
              />
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label className="form-label" style={{ margin: 0 }}>Artisan Story & Technical Description *</label>
                <VoiceInputButton
                  onTranscript={(text) => setCatalogDescription((prev) => (prev ? `${prev} ${text}` : text))}
                  placeholder="Speak your story..."
                />
              </div>
              <textarea
                className="form-control"
                rows={4}
                required
                placeholder="Highlight craft heritage, material sustainably sourced, and utility..."
                value={catalogDescription}
                onChange={(e) => setCatalogDescription(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Search Keywords (comma-separated) *</label>
              <input
                type="text"
                className="form-control"
                required
                placeholder="bamboo, storage, handwoven, sustainable, basket"
                value={catalogKeywords}
                onChange={(e) => setCatalogKeywords(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Material *</label>
                <input
                  type="text"
                  className="form-control"
                  required
                  value={catalogMaterial}
                  onChange={(e) => setCatalogMaterial(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Craft Technique</label>
                <input
                  type="text"
                  className="form-control"
                  value={catalogCraftType}
                  onChange={(e) => setCatalogCraftType(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Color / Finish</label>
                <input
                  type="text"
                  className="form-control"
                  value={catalogColor}
                  onChange={(e) => setCatalogColor(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Intended Purpose</label>
                <input
                  type="text"
                  className="form-control"
                  value={catalogPurpose}
                  onChange={(e) => setCatalogPurpose(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }} disabled={isLoading}>
              <CheckCircle2 size={16} />
              <span>Approve Catalog & Proceed to Pricing</span>
            </button>
          </form>
        )}

        {/* STEP 4: DYNAMIC PRICING */}
        {currentStep === 4 && workflow && (
          <form onSubmit={handleCalculatePricing}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Step 4: Dynamic Pricing Agent</h2>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                Deterministic Decimal calculations ensure your selling price covers all direct costs,
                commission, and secures your target profit margin.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Raw Material Cost (₹)</label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  value={materialCost}
                  onChange={(e) => setMaterialCost(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Artisan Labor Cost (₹)</label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  value={laborCost}
                  onChange={(e) => setLaborCost(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Packaging Cost (₹)</label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  value={packagingCost}
                  onChange={(e) => setPackagingCost(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Allocated Overhead (₹)</label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  value={overheadCost}
                  onChange={(e) => setOverheadCost(Number(e.target.value))}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Seller Shipping Expense (₹)</label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  value={shippingCost}
                  onChange={(e) => setShippingCost(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Marketplace Fee (%)</label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  max="90"
                  value={marketplaceCommission}
                  onChange={(e) => setMarketplaceCommission(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Target Profit Margin (%)</label>
                <input
                  type="number"
                  className="form-control"
                  min="1"
                  max="80"
                  value={targetMargin}
                  onChange={(e) => setTargetMargin(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Rounding Policy</label>
                <select
                  className="form-control"
                  value={pricingStrategy}
                  onChange={(e: any) => setPricingStrategy(e.target.value)}
                >
                  <option value="round_nearest_rupee">Nearest Rupee</option>
                  <option value="exact">Exact (2 Decimals)</option>
                  <option value="psychological_99">Ending in ₹99</option>
                </select>
              </div>
            </div>

            {/* Live Pricing Breakdown Card */}
            {workflow.pricing && (
              <div
                style={{
                  background: 'var(--color-bg-subtle)',
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  margin: '1rem 0',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Recommended Selling Price</span>
                    <h3 style={{ fontSize: '1.75rem', color: 'var(--color-primary)' }}>
                      ₹{workflow.pricing.suggested_selling_price.toLocaleString('en-IN')}
                    </h3>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Estimated Net Profit</span>
                    <h4 style={{ fontSize: '1.25rem', color: 'var(--color-success)' }}>
                      ₹{workflow.pricing.estimated_profit.toLocaleString('en-IN')} ({workflow.pricing.estimated_profit_margin_percent}%)
                    </h4>
                  </div>
                </div>
              </div>
            )}

            <button type="submit" className="btn btn-primary" style={{ marginTop: '0.5rem' }} disabled={isLoading}>
              <Calculator size={16} />
              <span>Calculate Price & Proceed to Inventory</span>
            </button>
          </form>
        )}

        {/* STEP 5: INVENTORY & CAPACITY */}
        {currentStep === 5 && workflow && (
          <form onSubmit={handleSaveInventory}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Step 5: Inventory & Operational Capacity</h2>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                Set your ready stock, monthly handcrafting capacity, and production turnaround times.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Ready Stock (Units Available)</label>
                <input
                  type="number"
                  className="form-control"
                  min="0"
                  value={availableQuantity}
                  onChange={(e) => setAvailableQuantity(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Monthly Production Capacity (Units)</label>
                <input
                  type="number"
                  className="form-control"
                  min="1"
                  value={monthlyCapacity}
                  onChange={(e) => setMonthlyCapacity(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Minimum Order Quantity (MOQ)</label>
                <input
                  type="number"
                  className="form-control"
                  min="1"
                  value={moq}
                  onChange={(e) => setMoq(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Production Lead Time (Days)</label>
                <input
                  type="number"
                  className="form-control"
                  min="1"
                  value={leadTimeDays}
                  onChange={(e) => setLeadTimeDays(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Workshop Location (City, State, Country)</label>
              <input
                type="text"
                className="form-control"
                value={workshopLocation}
                onChange={(e) => setWorkshopLocation(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }} disabled={isLoading}>
              <CheckCircle2 size={16} />
              <span>Save Inventory & Discover Buyer Matches</span>
            </button>
          </form>
        )}

        {/* STEP 6: MARKET LINKAGE MATCHES */}
        {currentStep === 6 && workflow && (
          <div>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Step 6: Genuine Market Linkages</h2>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                The Market Linkage Agent evaluated active buyer requirements in MongoDB against your craft specifications.
              </p>
            </div>

            {matches.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2.5rem 1rem', background: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)' }}>
                <Compass size={32} color="var(--color-primary)" style={{ marginBottom: '0.5rem' }} />
                <h4>No Immediate High-Affinity Matches</h4>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
                  No active buyers currently seeking this exact spec. You can still proceed to publish your listing.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                {matches.map((m) => (
                  <div
                    key={m.match_id}
                    style={{
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      padding: '1.25rem',
                      background: 'white',
                      boxShadow: 'var(--shadow-sm)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                      <div>
                        <h4 style={{ fontSize: '1.1rem' }}>{m.buyer_name}</h4>
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                          {m.buyer_type} • Location: {m.buyer_summary.delivery_location}
                        </span>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <span
                          style={{
                            fontSize: '1.25rem',
                            fontWeight: 800,
                            fontFamily: 'var(--font-heading)',
                            color: m.match_score >= 80 ? 'var(--color-success)' : 'var(--color-primary)',
                          }}
                        >
                          {m.match_score}%
                        </span>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
                          {m.match_category} Match
                        </div>
                      </div>
                    </div>

                    {/* Compatibility Grid */}
                    <div className="compat-grid">
                      <div className={`compat-item ${m.compatibility.category}`}>
                        <span>Category</span>
                        <span>{m.compatibility.category ? '✓' : '✗'}</span>
                      </div>
                      <div className={`compat-item ${m.compatibility.budget}`}>
                        <span>Budget</span>
                        <span>{m.compatibility.budget ? '✓' : '✗'}</span>
                      </div>
                      <div className={`compat-item ${m.compatibility.quantity}`}>
                        <span>Quantity</span>
                        <span>{m.compatibility.quantity ? '✓' : '✗'}</span>
                      </div>
                      <div className={`compat-item ${m.compatibility.delivery}`}>
                        <span>Turnaround</span>
                        <span>{m.compatibility.delivery ? '✓' : '✗'}</span>
                      </div>
                    </div>

                    <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', margin: '0.5rem 0' }}>
                      <strong>Buyer Needs:</strong> {m.buyer_summary.required_quantity} units | Budget: {m.buyer_summary.budget_range}
                    </p>

                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-main)', background: 'var(--color-primary-light)', padding: '0.6rem 0.8rem', borderRadius: 'var(--radius-sm)' }}>
                      <strong>Recommendation:</strong> {m.recommendation}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
              <button className="btn btn-outline" onClick={() => setCurrentStep(5)}>
                &lt; Back to Inventory
              </button>
              <button className="btn btn-primary" onClick={() => setCurrentStep(7)}>
                <span>Proceed to Final Publication</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 7: PUBLISH & REVIEW */}
        {currentStep === 7 && workflow && (
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: workflow.workflow_status === 'published' ? 'var(--color-success-bg)' : 'var(--color-primary-light)',
                color: workflow.workflow_status === 'published' ? 'var(--color-success)' : 'var(--color-primary)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
              }}
            >
              {workflow.workflow_status === 'published' ? <CheckCircle2 size={36} /> : <Sparkles size={36} />}
            </div>

            <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
              {workflow.workflow_status === 'published' ? 'Product Successfully Published!' : 'Ready to Publish Your Craft?'}
            </h2>
            <p style={{ color: 'var(--color-text-muted)', maxWidth: '540px', margin: '0 auto 2rem', fontSize: '0.9rem' }}>
              {workflow.workflow_status === 'published'
                ? 'Your product listing is live on the marketplace. Verified buyers and wholesalers can discover and send sourcing inquiries.'
                : 'All four AI agents have successfully processed your listing: enhanced photography, storytelling catalog, profit-guaranteed price, and verified market linkages.'}
            </p>

            {workflow.workflow_status !== 'published' ? (
              <button
                className="btn btn-primary"
                onClick={handlePublish}
                disabled={isLoading}
                style={{ padding: '0.85rem 2rem', fontSize: '1.05rem' }}
              >
                <span>Publish Craft to Marketplace</span>
                <Send size={18} />
              </button>
            ) : (
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                <button
                  className="btn btn-primary"
                  onClick={() => onNavigate('artisan-dashboard')}
                >
                  Return to Studio Dashboard
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
