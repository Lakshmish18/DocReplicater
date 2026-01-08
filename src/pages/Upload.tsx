import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, FileText, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { apiService } from '../services/api';

export default function Upload() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file: File) => {
    const allowedTypes = [
      'application/pdf', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/png',
      'image/jpeg',
      'image/tiff'
    ];
    const allowedExtensions = ['.pdf', '.docx', '.png', '.jpg', '.jpeg', '.tiff', '.tif'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      setError('Invalid file type. Please upload a DOCX, PDF, or image file.');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setError('File size exceeds 50MB limit.');
      return;
    }

    setUploadedFile(file);
    setError(null);
  };

  const handleUpload = async () => {
    if (!uploadedFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await apiService.uploadDocument(uploadedFile);
      setDocumentId(response.document_id);
      // Store document ID in sessionStorage for editor page
      sessionStorage.setItem('documentId', response.document_id);
      navigate('/editor');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
      setIsUploading(false);
    }
  };

  const handleProceed = () => {
    if (documentId) {
    navigate('/editor');
    } else {
      handleUpload();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Upload Document</h1>
          <p className="mt-2 text-gray-600">
            Upload your report to extract its design and formatting
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {!uploadedFile ? (
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragging
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <UploadIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Drag and drop your document here
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                or click to browse files
              </p>
              
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".docx,.pdf,.png,.jpg,.jpeg,.tiff,.tif"
                onChange={handleFileInput}
              />
              <label
                htmlFor="file-upload"
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium cursor-pointer transition-colors inline-block"
              >
                Choose File
              </label>
              
              <div className="mt-6 text-xs text-gray-500">
                <p className="font-medium mb-1">Supported formats:</p>
                <p>• DOCX files (recommended for best fidelity)</p>
                <p>• PDF files (auto-converted to DOCX)</p>
                <p>• Images (PNG, JPG, TIFF) - OCR + conversion</p>
                <p className="mt-2 text-blue-600">All files converted to DOCX for 100% design preservation</p>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {documentId ? 'File uploaded successfully' : 'File selected'}
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-center">
                  <FileText className="h-5 w-5 text-gray-600 mr-2" />
                  <span className="text-sm font-medium text-gray-700">{uploadedFile.name}</span>
                </div>
              </div>
              <button
                onClick={handleProceed}
                disabled={isUploading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-8 py-3 rounded-lg font-medium transition-colors w-full flex items-center justify-center"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : documentId ? (
                  'Proceed to Edit'
                ) : (
                  'Upload & Proceed'
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}