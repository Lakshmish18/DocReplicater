# DocReplicate - Document Design Replicator

A powerful full-stack application that extracts design and formatting from existing documents (DOCX, PDF, Images) and allows you to generate new documents with your own content while preserving 100% of the original professional formatting.

## 🎯 Features

- 📄 **Multi-Format Support**: Upload DOCX, PDF, or images (PNG, JPG, TIFF, BMP)
- 🎨 **100% Design Preservation**: Maintains all colors, fonts, borders, spacing, and layout
- ✏️ **Content Editing**: Edit text content section-by-section while design remains locked
- 🤖 **AI Content Generation**: Use OpenAI to generate content for any section
- 📥 **Export Options**: Download as DOCX (100% fidelity) or PDF
- 🔄 **Universal Parser**: Works with any document structure - simple or complex templates

## 🛠️ Tech Stack

### Frontend
- React 18 + TypeScript
- Vite (Build Tool)
- Tailwind CSS (Styling)
- React Router (Navigation)
- Lucide React (Icons)

### Backend
- FastAPI (Python Web Framework)
- python-docx (DOCX Processing)
- PyMuPDF (PDF Processing)
- Tesseract OCR (Image/Scanned PDF Processing)
- OpenAI API (Content Generation)
- Uvicorn (ASGI Server)

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1. **Node.js** (v18 or higher)
   - Download from: https://nodejs.org/
   - Verify: `node --version`

2. **Python** (3.8 or higher)
   - Download from: https://www.python.org/downloads/
   - Verify: `python --version` or `python3 --version`

3. **OpenAI API Key**
   - Get one from: https://platform.openai.com/api-keys
   - You'll need this for AI content generation

4. **Tesseract OCR** (Optional, for image/scanned PDF support)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

---

## 🚀 Complete Setup Guide

### Step 1: Clone or Download the Project

If you have the project files, navigate to the project directory:
```bash
cd /path/to/DocReplicate
```

### Step 2: Backend Setup

#### 2.1 Navigate to Backend Directory
```bash
cd backend
```

#### 2.2 Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

#### 2.3 Install Python Dependencies
```bash
pip install -r requirements.txt
```

This will install all required packages including FastAPI, python-docx, OpenAI, etc.

#### 2.4 Create Environment File

Create a `.env` file in the `backend` directory:

```bash
# On macOS/Linux
touch .env

# On Windows
type nul > .env
```

Then open `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Important:** Replace `sk-your-openai-api-key-here` with your actual OpenAI API key.

#### 2.5 Verify Backend Setup

Start the backend server:
```bash
python run.py
```

You should see:
```
============================================================
Starting Document Design Replicator
Version: 1.0.0
Environment: development
============================================================

Server: http://0.0.0.0:8000
API Docs: http://0.0.0.0:8000/docs
```

The backend is now running on `http://localhost:8000`

**Keep this terminal window open!**

### Step 3: Frontend Setup

#### 3.1 Open a New Terminal Window

Keep the backend running, and open a new terminal window/tab.

#### 3.2 Navigate to Project Root
```bash
cd /path/to/DocReplicate
```

#### 3.3 Install Node Dependencies
```bash
npm install
```

This will install all React dependencies (React, Vite, Tailwind, etc.)

#### 3.4 Start Frontend Development Server
```bash
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

The frontend is now running on `http://localhost:5173`

### Step 4: Access the Application

1. Open your web browser
2. Navigate to: `http://localhost:5173`
3. You should see the Document Replicator interface!

---

## 📖 Usage Guide

### Uploading a Document

1. Click **"Upload Document"** or drag and drop a file
2. Supported formats:
   - **DOCX** (Word documents) - Best for 100% design preservation
   - **PDF** (Text-based or scanned) - Automatically converted to DOCX
   - **Images** (PNG, JPG, TIFF, BMP) - Uses OCR to extract text

3. Wait for processing (usually a few seconds)

### Editing Content

1. After upload, you'll see the **Editor** page
2. **Left Panel**: 
   - Select a section from the list
   - Edit the content in the text area
   - Use AI to generate new content

3. **AI Content Generation**:
   - Enter a prompt describing what you want
   - Click "Generate Content"
   - Review the generated content
   - Click "Use This Content" to apply it

4. **Save Changes**:
   - Click "Save Changes" button
   - Button will turn yellow (saving) then green (saved)

### Exporting Your Document

1. Click **"Export Document"** button
2. Choose your format:
   - **Download as DOCX** (Recommended) - Preserves 100% of original design
   - **Download as PDF** - Basic formatting only

3. The file will download automatically

---

## 🔧 Configuration

### Backend Configuration

Edit `backend/.env`:
```env
OPENAI_API_KEY=your-key-here
```

### Frontend Configuration

The frontend automatically connects to `http://localhost:8000`. If your backend runs on a different port, edit `src/services/api.ts`:

```typescript
const API_BASE_URL = 'http://localhost:YOUR_PORT/api/v1';
```

---

## 🐛 Troubleshooting

### Backend Issues

**Problem: `ModuleNotFoundError: No module named 'docx'`**
- **Solution**: Make sure virtual environment is activated and run `pip install -r requirements.txt`

**Problem: `ERR_CONNECTION_REFUSED`**
- **Solution**: Ensure backend is running on port 8000. Check with `curl http://localhost:8000/health`

**Problem: `OPENAI_API_KEY not found`**
- **Solution**: Create `.env` file in `backend/` directory with your API key

**Problem: Port 8000 already in use**
- **Solution**: Kill the process using port 8000:
  ```bash
  # macOS/Linux
  lsof -ti:8000 | xargs kill -9
  
  # Windows
  netstat -ano | findstr :8000
  taskkill /PID <PID> /F
  ```

### Frontend Issues

**Problem: `npm install` fails**
- **Solution**: 
  - Clear npm cache: `npm cache clean --force`
  - Delete `node_modules` and `package-lock.json`
  - Run `npm install` again

**Problem: Frontend can't connect to backend**
- **Solution**: 
  - Verify backend is running: `curl http://localhost:8000/health`
  - Check browser console for CORS errors
  - Ensure both are running on correct ports

**Problem: Page shows blank/white screen**
- **Solution**: 
  - Open browser console (F12)
  - Check for JavaScript errors
  - Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

### Document Processing Issues

**Problem: Document shows empty in editor**
- **Solution**: 
  - The document might have complex structure
  - Try a simpler document first
  - Check backend logs for extraction errors

**Problem: Exported document missing images/graphics**
- **Solution**: 
  - Use DOCX export (not PDF) for best results
  - Ensure original document has embedded images (not linked)

**Problem: Colors not preserved in export**
- **Solution**: 
  - Export as DOCX format (not PDF)
  - DOCX preserves 100% of formatting including colors

---

## 📁 Project Structure

```
DocReplicate/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── application/  # Business logic
│   │   ├── domain/       # Domain entities
│   │   └── infrastructure/ # External services
│   ├── uploads/          # Uploaded files
│   ├── outputs/         # Generated documents
│   ├── .env             # Environment variables
│   ├── requirements.txt  # Python dependencies
│   └── run.py           # Server entry point
├── src/
│   ├── pages/           # React pages
│   ├── services/        # API service
│   ├── components/      # React components
│   └── App.tsx          # Main app component
├── package.json         # Node dependencies
└── README.md           # This file
```

---

## 🔐 Security Notes

- **Never commit `.env` files** to version control
- **Keep your OpenAI API key secret** - don't share it publicly
- For production, add:
  - Authentication/authorization
  - Rate limiting
  - Input validation
  - File size limits
  - Secure file storage

---

## 🚀 Production Deployment

### Backend (FastAPI)

1. Use a production ASGI server:
   ```bash
   pip install gunicorn uvicorn[standard]
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. Set environment variables:
   ```env
   ENVIRONMENT=production
   OPENAI_API_KEY=your-key
   ```

3. Use a reverse proxy (Nginx) for HTTPS

### Frontend (React)

1. Build for production:
   ```bash
   npm run build
   ```

2. Serve with a web server:
   ```bash
   npm install -g serve
   serve -s dist
   ```

---

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review backend logs in the terminal
3. Check browser console (F12) for frontend errors
4. Verify all prerequisites are installed

---

## 📄 License

MIT License

---

## 🎉 You're All Set!

Your Document Replicator is now ready to use. Start by uploading a document and see how it preserves the design while letting you edit the content!

**Happy Document Replicating!** 🚀
