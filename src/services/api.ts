const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface DocumentStructure {
  id: string;
  type?: string; // Legacy field
  section_type: string; // Backend uses this
  content: string;
  style?: string;
  style_token?: string;
  format?: any;
  runs?: Array<{ text: string; format: any }>;
  editable?: boolean;
  [key: string]: any;
}

export interface DocumentData {
  id: string;
  original_filename: string;
  design_schema: any;
  sections: DocumentStructure[];
}

export interface UploadResponse {
  success: boolean;
  document_id: string;
  design_schema: any;
  sections: DocumentStructure[];
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }

    const result = await response.json();
    const data = result.data; // Backend wraps response in 'data' field
    
    // Map response to expected format
    // Structure: data.document.id, data.design_schema, data.sections
    return {
      success: true,
      document_id: data.document.id,
      design_schema: data.design_schema,
      sections: data.sections || [],
    };
  }

  async getDocument(documentId: string): Promise<DocumentData> {
    const result = await this.request<any>(`/documents/${documentId}`);
    const data = result.data; // Backend wraps response in 'data' field
    // Structure: data.document, data.design_schema, data.sections
    return {
      id: data.document.id,
      original_filename: data.document.original_filename,
      design_schema: data.design_schema,
      sections: data.sections || [],
    };
  }

  async updateContent(documentId: string, structure: DocumentStructure[]): Promise<{ success: boolean; message: string }> {
    // Update sections using batch update
    // Backend expects: { sections: [{ id, content }, ...] }
    const sections = structure.map(section => ({
      id: section.id,
      content: section.content,
    }));
    
    return this.request(`/documents/${documentId}/sections/batch-update`, {
      method: 'POST',
      body: JSON.stringify({ sections }),
    });
  }

  async generateContent(
    documentId: string,
    sectionId: string,
    prompt: string
  ): Promise<{ content: string }> {
    const result = await this.request<any>(`/documents/${documentId}/ai/generate`, {
      method: 'POST',
      body: JSON.stringify({ 
        section_id: sectionId, 
        prompt,
        tone: 'professional',
      }),
    });
    // Backend returns: { success: true, data: { content: "...", ... } }
    return {
      content: result.data.content,
    };
  }

  async generateDocument(documentId: string, format: 'pdf' | 'docx' = 'docx'): Promise<{ success: boolean; download_url: string }> {
    const result = await this.request<any>(`/documents/${documentId}/export`, {
      method: 'POST',
      body: JSON.stringify({ format }),
    });
    return {
      success: true,
      download_url: `/documents/${documentId}/export/download/${format}`,
    };
  }

  async downloadDocument(documentId: string, format: 'pdf' | 'docx'): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/export/download/${format}`, {
      method: 'GET',
    });
    if (!response.ok) {
      throw new Error('Download failed');
    }
    return response.blob();
  }

  async deleteDocument(documentId: string): Promise<{ success: boolean; message: string }> {
    await this.request(`/documents/${documentId}`, {
      method: 'DELETE',
    });
    return { success: true, message: 'Document deleted' };
  }
}

export const apiService = new ApiService();

