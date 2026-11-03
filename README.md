# KarigarConnect 🏺✨

> **AI-Powered Artisan Empowerment & Direct Market Linkage Ecosystem**  
> Digitizing India's traditional artisans with studio-grade AI image enhancement, Gemini catalog generation, deterministic dynamic pricing, voice-to-text dictation, and verifiable B2B market linkage.

---

## 🌟 Highlights & Capabilities

KarigarConnect coordinates **4 dedicated AI and deterministic agents** to solve the primary economic challenges faced by traditional artisans:

1. **Agent 1: Studio Image Processing Engine**
   - Pure white background studio isolation (`studio_white`) conforming to Amazon/Etsy listing standards.
   - 3 selectable aesthetic styles:
     - `Studio Pure White` — 1200×1200 framing, crisp contrast, pure `#FFFFFF` studio isolation.
     - `Warm Heritage & Craft Glow` — Warm ivory backdrop, enriched amber saturation, soft contact shadow.
     - `Modern Minimalist Gallery` — Neutral studio gray, crisp drop shadow, editorial micro-contrast.
   - Automatic bounding-box framing, centering, and brightness/contrast enhancement.

2. **Agent 2: Intelligent Catalog Generation Agent**
   - Google Gemini 2.5 Flash integration with prompt engineering for craft-specific listings.
   - Generates SEO-optimized titles, 8 targeted e-commerce search keywords, and an authentic heritage story.
   - Resilient multi-tier fallback with a 4.5s timeout: immediately falls back to a deterministic craft knowledge engine if Gemini quota or network is unavailable.

3. **Agent 3: Dynamic Pricing Recommendation Engine**
   - Comprehensive cost categorization: raw material, labor, packaging, overhead, and fulfillment.
   - Margin-based pricing logic factoring in marketplace commission (10%) and target artisan margin (25%).
   - Scenario analysis: exact cost-plus, round nearest Rupee, and psychological (`.99`) pricing.
   - Complete statutory disclaimer handling and margin verification.

4. **Agent 4: Market Linkage & Matching Agent**
   - Deterministic multi-factor scoring matching published products against genuine active buyer requirements.
   - Factors evaluated: category match, material compatibility, craft technique, price/budget alignment, batch quantity/MOQ, fulfillment lead time, and regional delivery capability.
   - Categorized tiers: `High compatibility`, `Eligible with minor adjustments`, or `Not eligible`.

5. **🎙️ Voice-to-Text Dictation**
   - Native HTML5 Web Speech API integration (`SpeechRecognition`) for artisans who prefer dictating in spoken Hindi/English rather than typing.
   - Available on Product Name, Crafting Technique, and Story/Description inputs.

---

## 🏗️ Architecture & Tech Stack

```text
KarigarConnect/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agent routes (image, catalog, pricing, linkage, workflow, auth, admin)
│   │   ├── database/        # MongoDB connection with automatic mongomock fallback
│   │   ├── middleware/      # Rate limiter, unified error handling
│   │   ├── schemas/         # Pydantic v2 schemas for all requests & responses
│   │   ├── services/        # Business logic & core engines (image, pricing, linkage, etc.)
│   │   └── main.py          # FastAPI application & single-port SPA mounting
│   └── tests/               # Pytest suite (71 tests passing)
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, VoiceInputButton, etc.
│   │   ├── context/         # AuthContext with auto-recovery and timeouts
│   │   ├── pages/           # ArtisanDashboard, ProductWorkflowWizard, BuyerDashboard, Admin, etc.
│   │   ├── services/        # Centralized typed API service (dynamic host resolution)
│   │   └── types/           # TypeScript domain types & interfaces
│   ├── package.json
│   └── vite.config.ts
└── docs/                    # Technical architecture & specification docs
```

- **Backend:** Python 3.11+, FastAPI, Uvicorn, Pillow (PIL), NumPy, Pydantic v2, PyMongo, Google GenAI SDK.
- **Database:** MongoDB Atlas (with automatic in-memory `mongomock` fallback for local/offline environments).
- **Frontend:** React 19, TypeScript, Vite, Lucide Icons, Vanilla CSS Design System.
- **Testing:** Pytest, HTTPX (71 automated backend tests).

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Git

### 2. Backend Setup
```bash
# Clone the repository
git clone <YOUR_REPOSITORY_URL>
cd KarigarConnect

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Running the Unified Application (Single Port 8000)
The FastAPI backend directly serves the prebuilt React SPA and all API endpoints from port `8000`, eliminating CORS issues and allowing seamless mobile testing over Wi-Fi / USB tethering:

```bash
# From workspace root with virtual environment activated:
set PYTHONPATH=.
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open in your browser:
- **PC:** `http://localhost:8000`
- **API Docs (Swagger UI):** `http://localhost:8000/docs`
- **Mobile Devices (Same Wi-Fi or USB Tethering):** `http://<YOUR_LAN_IP>:8000`

### 5. Running in Development Mode (Vite Hot-Reloading)
To develop frontend components with live HMR:
```bash
# Terminal 1 (Backend):
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 (Frontend Dev Server):
npm --prefix frontend run dev
```
Open: `http://localhost:5173`

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
set PYTHONPATH=.
pytest backend/tests
```
*Current test status: 71 passed.*

---

## 🔑 Default Bootstrap Accounts
When starting with an empty database or in-memory fallback, the following administrative account is automatically verified at boot:
- **Admin Email:** `admin@karigarconnect.com`
- **Admin Password:** `Admin@Karigar2026`
*(Artisans and Buyers can register directly via the `/register` page).*

---

## 📄 License
This project is open-source under the MIT License.
