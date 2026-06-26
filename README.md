# ModSync: Curriculum Review Engine (Hackathon MVP)

**ModSync** is an AI-powered, faculty-assistive curriculum modernization platform. 

Faculty members simply upload a module syllabus (PDF). The platform's multi-agent AI engine extracts the text and images, detects outdated technologies, scores them on a strict 100-point lifecycle risk rubric, and generates a side-by-side **Migration Assistant** to help faculty confidently transition to modern industry standards.

The app is intentionally framed as an **active decision support and teaching tool**. It does not make curriculum decisions for the faculty; instead, it provides visual evidence, side-by-side code comparisons, and actionable migration strategies.

---

## 🏗️ Architecture: The Monolithic Dual-Agent Fallback Engine

Our engine (`agentic_pipeline.py`) is built to be fast, mathematically accurate, and virtually uncrashable.

1. **Agent 1 (The Scout):** Rapidly scans the PDF text and images to extract a raw list of technologies, frameworks, and tools.
2. **Agent 2 (The Super Analyst):** Evaluates the lifecycle risk of the extracted tools using strict mathematical constraints. Simultaneously, it generates a comprehensive Migration Strategy (comparing deprecated contexts vs. modern equivalents).
3. **Dual-Multimodal Processing:** Uses `PyMuPDF` and `PIL` to extract actual screenshots, architecture diagrams, and logos from the curriculum PDF. These images are converted to Base64 and evaluated directly by the LLMs.
4. **Resilient Fallback Loop:** The system defaults to **OpenAI**. If rate limits or quota errors occur, the backend gracefully catches the crash and instantly reroutes the exact same multimodal payload to other **OpenAI models** (such as GPT-4o-mini or GPT-4o) without the user ever noticing.
5. **Programmatic Math Overrides:** To prevent LLM "hallucinations" on scoring, Agent 2 is restricted by strict JSON schemas. The final 100-point priority score is intercepted and mathematically recalculated by Python, ensuring 100% accurate results.

---

## 🤖 AI Usage Disclosure

*   **Core Product Engine:** We integrated **OpenAI (GPT-4o)** and other **OpenAI models** APIs to create the multi-agent curriculum reviewer. We engineered the resilient fallback loop and multimodal integration natively.
*   **AI Pair Programming:** We heavily utilized **Google Antigravity** as our AI Pair Programmer to accelerate prototyping. Antigravity helped architect the Python backend, refactor the Next.js frontend UI layouts, surgically merge branch features (Migration UI), and debug complex Python scope errors (`UnboundLocalError`).
*   **Testing & Validation:** Conversational LLMs (Claude/ChatGPT) were used to generate highly specific, multi-disciplinary "mock syllabi" designed to stress-test our system with deliberate edge cases.

---

## 💻 Tech Stack & Dependencies

*   **Frontend:** Next.js, React, TypeScript, TailwindCSS, `lucide-react`
*   **Backend:** FastAPI, Python, SQLite
*   **PDF Processing:** `PyMuPDF` (primary path for text and image blob extraction), `PIL` (Image processing)
*   **AI SDKs:** `openai`

---

## 🚀 Access & Setup Instructions

### 1. Environment Variables
You must configure your API keys in the backend directory.
```powershell
cd backend
copy .env.example .env
```
Edit the `.env` file and add your keys:
```env
OPENAI_API_KEY="sk-..."
```
*(Note: An OpenAI API key is required to connect to the LLM backend for processing).*

### 2. Run the Backend (FastAPI)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Run the Frontend (Next.js)
Open a new terminal window:
```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

### 4. Use the Platform
1. Open `http://localhost:3000` in your browser.
2. Upload a sample syllabus PDF.
3. Watch the backend terminal to see the Resilient Fallback Engine and Dual-Agents in action.
4. View the generated **Migration Assistant** on the frontend, featuring side-by-side legacy vs. modern code snippets.
