import { Link } from 'react-router-dom';
import { Upload, CreditCard as Edit3, Download, ArrowRight } from 'lucide-react';

export default function Home() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="lg:grid lg:grid-cols-12 lg:gap-8 items-center">
            <div className="lg:col-span-6">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
                Reuse Any Report Design.{' '}
                <span className="text-blue-600">Change Only the Content.</span>
              </h1>
              <p className="mt-6 text-xl text-gray-600 leading-relaxed">
                Upload a well-formatted report and generate your own version without breaking design or layout.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row gap-4">
                <Link
                  to="/upload"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-medium text-lg transition-colors inline-flex items-center justify-center"
                >
                  Upload Document
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
                <a
                  href="#how-it-works"
                  className="border border-gray-300 hover:border-gray-400 text-gray-700 px-8 py-4 rounded-lg font-medium text-lg transition-colors inline-flex items-center justify-center"
                >
                  See How It Works
                </a>
              </div>
            </div>
            <div className="mt-12 lg:mt-0 lg:col-span-6">
              <div className="bg-gray-50 rounded-xl p-8 border border-gray-200">
                <div className="space-y-4">
                  <div className="bg-white p-4 rounded-lg border border-gray-200">
                    <div className="h-3 bg-blue-600 rounded w-3/4 mb-3"></div>
                    <div className="space-y-2">
                      <div className="h-2 bg-gray-200 rounded w-full"></div>
                      <div className="h-2 bg-gray-200 rounded w-5/6"></div>
                      <div className="h-2 bg-gray-200 rounded w-4/5"></div>
                    </div>
                  </div>
                  <div className="text-center text-sm text-gray-500">
                    Document preview with preserved formatting
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">How it Works</h2>
            <p className="mt-4 text-xl text-gray-600">Three simple steps to replicate any document design</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-xl border border-gray-200 text-center hover:shadow-lg transition-shadow">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Upload Document</h3>
              <p className="text-gray-600 leading-relaxed">
                DOCX and text-based PDF support. We extract the design and formatting automatically.
              </p>
            </div>

            <div className="bg-white p-8 rounded-xl border border-gray-200 text-center hover:shadow-lg transition-shadow">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <Edit3 className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Edit Content Only</h3>
              <p className="text-gray-600 leading-relaxed">
                Replace text while formatting and design remain locked. Focus on content, not layout.
              </p>
            </div>

            <div className="bg-white p-8 rounded-xl border border-gray-200 text-center hover:shadow-lg transition-shadow">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <Download className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Export Clean Report</h3>
              <p className="text-gray-600 leading-relaxed">
                Download as PDF or DOCX with your content in the original professional format.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}