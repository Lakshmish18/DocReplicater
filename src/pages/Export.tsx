import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CheckCircle, Download, CreditCard as Edit, Loader2, AlertCircle } from 'lucide-react';
import { apiService } from '../services/api';

export default function Export() {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const id = sessionStorage.getItem('documentId');
    if (!id) {
      navigate('/upload');
      return;
    }
    setDocumentId(id);
  }, [navigate]);

  const handleDownload = async (format: 'pdf' | 'docx') => {
    if (!documentId) return;

    try {
      setGenerating(true);
      setError(null);

      // First generate the document
      await apiService.generateDocument(documentId, format);

      // Then download it - force download, don't open
      const blob = await apiService.downloadDocument(documentId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `replicated_document.${format}`;
      a.setAttribute('download', `replicated_document.${format}`); // Force download
      a.setAttribute('target', '_self'); // Don't open in new tab
      a.style.display = 'none'; // Hide the link
      document.body.appendChild(a);
      
      // Force download by programmatically clicking
      const clickEvent = new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: false
      });
      a.dispatchEvent(clickEvent);
      
      // Clean up after a short delay to ensure download starts
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        if (document.body.contains(a)) {
          document.body.removeChild(a);
        }
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setGenerating(false);
    }
  };

  if (!documentId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900">Your report is ready</h1>
          <p className="mt-2 text-gray-600">
            Document has been processed with your content and original formatting
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Download Options</h2>

            <div className="space-y-3">
              {/* DOCX is primary - preserves 100% design fidelity */}
              <button
                onClick={() => handleDownload('docx')}
                disabled={generating}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-4 rounded-lg font-medium transition-colors flex items-center justify-center"
              >
                {generating ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="h-5 w-5 mr-2" />
                    Download as DOCX
                  </>
                )}
              </button>
              <p className="text-xs text-center text-green-600 -mt-1">
                ✓ Recommended - Preserves 100% original design
              </p>

              <button
                onClick={() => handleDownload('pdf')}
                disabled={generating}
                className="w-full border border-gray-300 hover:border-gray-400 disabled:opacity-50 text-gray-700 px-6 py-4 rounded-lg font-medium transition-colors flex items-center justify-center"
              >
                {generating ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="h-5 w-5 mr-2" />
                    Download as PDF
                  </>
                )}
              </button>
              <p className="text-xs text-center text-gray-500 -mt-1">
                Basic formatting only
              </p>
            </div>
          </div>

          <div className="pt-6 border-t border-gray-200">
            <Link
              to="/editor"
              className="w-full text-center text-blue-600 hover:text-blue-700 font-medium transition-colors flex items-center justify-center"
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit Again
            </Link>
          </div>
        </div>

        <div className="mt-8 text-center">
          <Link
            to="/"
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
