import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, FileText, Sparkles, Loader2, AlertCircle, Save, Check, X, CheckCircle2 } from 'lucide-react';
import { apiService, DocumentStructure } from '../services/api';

export default function Editor() {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [sections, setSections] = useState<DocumentStructure[]>([]);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('');
  const [generatedContent, setGeneratedContent] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const id = sessionStorage.getItem('documentId');
    if (!id) {
      navigate('/upload');
      return;
    }
    setDocumentId(id);
    loadDocument(id);
  }, [navigate]);

  const loadDocument = async (id: string) => {
    try {
      setLoading(true);
      const doc = await apiService.getDocument(id);
      // Store original sections to preserve formatting
      const editableSections = doc.sections.filter(s => {
        const sectionType = s.section_type || s.type || 'paragraph';
        return s.editable !== false && sectionType !== 'table';
      });
      // Store original sections in a ref-like structure for format preservation
      editableSections.forEach(section => {
        if (!section.runs || section.runs.length === 0) {
          // If no runs, create one from content with empty format
          section.runs = [{ text: section.content || '', format: {} }];
        }
      });
      setSections(editableSections);
      if (editableSections.length > 0) {
        setActiveSection(editableSections[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const updateSection = (id: string, newContent: string) => {
    setSections(prev => 
      prev.map(section => {
        if (section.id === id) {
          // Preserve ALL original formatting data
          const originalFormat = section.format || {};
          const originalStyle = section.style || 'Normal';
          
          // Get format from first run, or create default format based on section type
          const sectionType = section.section_type || section.type || 'paragraph';
          let runFormat = {};
          if (section.runs && section.runs.length > 0) {
            runFormat = section.runs[0].format || {};
          } else {
            // Create default format based on section type
            if (sectionType === 'title') {
              runFormat = { font_size: 24, bold: true };
            } else if (sectionType.startsWith('heading')) {
              const level = parseInt(sectionType.replace('heading_', '')) || 1;
              runFormat = { font_size: 24 - (level * 2), bold: true };
            }
          }
          
          return {
            ...section, // Preserve all original properties
            content: newContent,
            style: originalStyle, // Preserve style
            format: originalFormat, // Preserve paragraph format
            runs: [{ 
              text: newContent, 
              format: runFormat // Preserve run formatting
            }]
          };
        }
        return section;
      })
    );
  };

  const handleSave = async () => {
    if (!documentId) return;

    try {
      console.log('Saving started...');
      setSaving(true);
      setSaveSuccess(false);
      setError(null);
      
      await apiService.updateContent(documentId, sections);
      
      // Keep saving state visible for at least 800ms so user can see it
      await new Promise(resolve => setTimeout(resolve, 800));
      
      console.log('Saving complete, showing success');
      setSaving(false);
      setSaveSuccess(true);
      
      // Show success for 2 seconds
      setTimeout(() => {
        setSaveSuccess(false);
      }, 2000);
    } catch (err) {
      console.error('Save error:', err);
      setError(err instanceof Error ? err.message : 'Failed to save changes');
      setSaveSuccess(false);
      setSaving(false);
    }
  };

  const handleGenerateContent = async () => {
    if (!documentId || !activeSection || !prompt.trim()) return;

    try {
      setGenerating(true);
      setError(null);
      setGeneratedContent(null);
      const response = await apiService.generateContent(documentId, activeSection, prompt);
      setGeneratedContent(response.content);
      setPrompt('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate content');
      setGeneratedContent(null);
    } finally {
      setGenerating(false);
    }
  };

  const handleAcceptGeneratedContent = () => {
    if (!activeSection || !generatedContent) return;
    updateSection(activeSection, generatedContent);
    setGeneratedContent(null);
  };

  const handleRejectGeneratedContent = () => {
    setGeneratedContent(null);
  };

  const handleExport = () => {
    if (documentId) {
      sessionStorage.setItem('documentId', documentId);
    }
    navigate('/export');
  };

  const activeContent = sections.find(s => s.id === activeSection)?.content || '';
  const activeSectionData = sections.find(s => s.id === activeSection);

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center pt-16">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error && sections.length === 0) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center pt-16 px-4">
        <div className="max-w-md w-full bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-red-900 mb-2">Error</h3>
              <p className="text-sm text-red-700 mb-4">{error}</p>
              <button
                onClick={() => navigate('/upload')}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                Go Back to Upload
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="flex h-screen pt-16">
        {/* Left Panel - Content Editor */}
        <div className="w-1/2 border-r border-gray-200 flex flex-col">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Content Editor</h2>
            <p className="text-sm text-gray-600 mt-1">Select a section to edit content</p>
          </div>
          
          {error && (
            <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-start">
              <AlertCircle className="h-4 w-4 text-red-600 mr-2 mt-0.5" />
              <p className="text-xs text-red-700">{error}</p>
            </div>
          )}

          <div className="flex-1 flex overflow-hidden">
            {/* Section List */}
            <div className="w-1/3 border-r border-gray-200 bg-gray-50 overflow-y-auto">
              <div className="p-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Sections</h3>
                <div className="space-y-1">
                  {sections.map(section => {
                    const sectionType = section.section_type || section.type || 'paragraph';
                    return (
                      <button
                        key={section.id}
                        onClick={() => {
                          setActiveSection(section.id);
                          setGeneratedContent(null); // Clear generated content when switching sections
                        }}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                          activeSection === section.id
                            ? 'bg-blue-100 text-blue-700 font-medium'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        {sectionType === 'title' ? 'Title' :
                         sectionType.startsWith('heading') ? `Heading ${sectionType.replace('heading_', '')}` :
                         sectionType === 'paragraph' ? 'Paragraph' : sectionType}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
            
            {/* Content Editor */}
            <div className="flex-1 p-6 overflow-y-auto">
              {activeSectionData && (
                <>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                      {(() => {
                        const sectionType = activeSectionData.section_type || activeSectionData.type || 'paragraph';
                        return sectionType === 'title' ? 'Title' :
                               sectionType.startsWith('heading') ? `Heading ${sectionType.replace('heading_', '')}` :
                               'Content';
                      })()}
                </label>
                <textarea
                  value={activeContent}
                      onChange={(e) => updateSection(activeSection!, e.target.value)}
                      className="w-full h-48 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your content here..."
                />
              </div>

                  {/* OpenAI Content Generation */}
                  <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Sparkles className="h-4 w-4 inline mr-1" />
                      Generate with AI
                    </label>
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      className="w-full h-20 p-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm mb-2"
                      placeholder="Describe what you want to write (e.g., 'Write an introduction about our company's growth in 2024')"
                    />
                    <button
                      onClick={handleGenerateContent}
                      disabled={generating || !prompt.trim()}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center"
                    >
                      {generating ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4 mr-2" />
                          Generate Content
                        </>
                      )}
                    </button>
                  </div>

                  {/* Generated Content Preview */}
                  {generatedContent && (
                    <div className="mb-4 p-4 bg-green-50 border-2 border-green-300 rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <label className="block text-sm font-semibold text-green-900">
                          <Sparkles className="h-4 w-4 inline mr-1" />
                          Generated Content Preview
                        </label>
                        <span className="text-xs text-green-700 bg-green-200 px-2 py-1 rounded">
                          Review before applying
                        </span>
                      </div>
                      <div className="bg-white border border-green-200 rounded p-3 mb-3 max-h-48 overflow-y-auto">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{generatedContent}</p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleAcceptGeneratedContent}
                          className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center"
                        >
                          <Check className="h-4 w-4 mr-2" />
                          Use This Content
                        </button>
                        <button
                          onClick={handleRejectGeneratedContent}
                          className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center"
                        >
                          <X className="h-4 w-4 mr-2" />
                          Discard
                        </button>
                      </div>
                    </div>
                  )}

              <p className="text-xs text-gray-500">
                Only content can be edited. Formatting and design are preserved.
              </p>
                </>
              )}
            </div>
          </div>
          
          <div className="p-6 border-t border-gray-200 space-y-3">
            <button
              onClick={handleSave}
              disabled={saving || saveSuccess}
              className={`w-full px-6 py-3 rounded-lg font-medium flex items-center justify-center text-white transition-all ${
                saveSuccess 
                  ? 'bg-green-600' 
                  : saving 
                    ? 'bg-yellow-500 cursor-wait' 
                    : 'bg-gray-600 hover:bg-gray-700'
              }`}
            >
              {saving ? (
                <span className="flex items-center">
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  <span>Saving...</span>
                </span>
              ) : saveSuccess ? (
                <span className="flex items-center">
                  <Check className="h-5 w-5 mr-2" />
                  <span>Saved!</span>
                </span>
              ) : (
                <span className="flex items-center">
                  <Save className="h-5 w-5 mr-2" />
                  <span>Save Changes</span>
                </span>
              )}
            </button>
            <button
              onClick={handleExport}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium"
            >
              Export Document
            </button>
          </div>
        </div>

        {/* Right Panel - Live Preview */}
        <div className="w-1/2 bg-gray-50">
          <div className="p-6 border-b border-gray-200 bg-white">
            <div className="flex items-center">
              <Eye className="h-5 w-5 text-gray-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">Live Preview</h2>
              <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                Design Locked
              </span>
            </div>
          </div>
          
          <div className="p-6 h-full overflow-y-auto">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 max-w-2xl">
              <div className="space-y-6">
                {sections.map(section => {
                  const sectionType = section.section_type || section.type || 'paragraph';
                  const isTitle = sectionType === 'title';
                  const isHeading = sectionType.startsWith('heading');
                  const headingLevel = sectionType.replace('heading_', '');

                  return (
                    <div
                      key={section.id}
                      className={isTitle ? 'text-center border-b border-gray-200 pb-6' : ''}
                    >
                      {isTitle ? (
                      <h1 className="text-3xl font-bold text-gray-900">{section.content}</h1>
                      ) : isHeading ? (
                      <div>
                          {headingLevel === '1' && <h1 className="text-2xl font-bold text-gray-900 mb-3">{section.content}</h1>}
                          {headingLevel === '2' && <h2 className="text-xl font-semibold text-gray-900 mb-3">{section.content}</h2>}
                          {headingLevel === '3' && <h3 className="text-lg font-semibold text-gray-900 mb-3">{section.content}</h3>}
                          {!headingLevel && <h2 className="text-xl font-semibold text-gray-900 mb-3">{section.content}</h2>}
                      </div>
                    ) : (
                        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{section.content}</p>
                    )}
                  </div>
                  );
                })}
              </div>
              
              <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="flex items-center text-xs text-gray-500">
                  <FileText className="h-4 w-4 mr-1" />
                  <span>Document Preview - Original formatting preserved</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
