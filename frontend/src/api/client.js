const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      errorData.detail || errorData.error || 'An error occurred',
      response.status,
      errorData
    );
  }
  return response.json();
}

export const api = {
  // Health check
  async health() {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return handleResponse(response);
  },

  // Zones - use search for large datasets
  async searchZones(query, limit = 50) {
    const params = new URLSearchParams({ q: query, limit: limit.toString() });
    const response = await fetch(`${API_BASE_URL}/api/zones/search?${params}`);
    return handleResponse(response);
  },

  async getZones(skip = 0, limit = 100) {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() });
    const response = await fetch(`${API_BASE_URL}/api/zones?${params}`);
    return handleResponse(response);
  },

  async getZoneRecords(zone, search = '', limit = 100) {
    const params = new URLSearchParams({ zone, limit: limit.toString() });
    if (search) params.append('search', search);
    const response = await fetch(`${API_BASE_URL}/api/zones/records?${params}`);
    return handleResponse(response);
  },

  // Requests
  async submitRequest(data) {
    const response = await fetch(`${API_BASE_URL}/api/requests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  async deleteRecord(zone, label, recordType) {
    const response = await fetch(`${API_BASE_URL}/api/zones/delete-record`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ zone, label, record_type: recordType }),
    });
    return handleResponse(response);
  },
};

export { APIError };
