function apiErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const issues = detail.map(issue => {
      if (!issue || typeof issue !== 'object') return '';
      const item = issue as { loc?: unknown; msg?: unknown };
      const location = Array.isArray(item.loc) ? item.loc.filter(part => part !== 'body').join('.') : '';
      const message = typeof item.msg === 'string' ? item.msg : 'Invalid request';
      return location ? `${location}: ${message}` : message;
    }).filter(Boolean);
    if (issues.length) return issues.join('; ');
  }
  if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') return detail.message;
  return fallback;
}

function responseFallback(status: number, fallback: string): string {
  if (status === 404) {
    return 'The investigation API route was not found. Check that the backend is deployed and API routing is configured, then try again.';
  }
  if ([502, 503, 504].includes(status)) {
    return 'The investigation service is temporarily unavailable. Check the backend deployment or retry shortly.';
  }
  if (status >= 500) {
    return `The investigation service returned a server error (HTTP ${status}). Retry shortly, and contact the operator if the problem continues.`;
  }
  return `${fallback} (HTTP ${status}).`;
}

export async function fetchApi(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error;
    throw new Error('Could not reach the investigation service. Check your connection or backend deployment, then try again.');
  }
}

export async function parseApiResponse<T>(response: Response, fallback: string): Promise<T> {
  let payload: unknown = null;
  if ((response.headers.get('content-type') || '').toLowerCase().includes('json')) {
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const detail = payload && typeof payload === 'object' && 'detail' in payload
      ? (payload as { detail?: unknown }).detail
      : undefined;
    throw new Error(apiErrorMessage(detail, responseFallback(response.status, fallback)));
  }

  if (payload === null) {
    throw new Error('The investigation service returned an empty or unreadable response. Try again, and contact the operator if the problem continues.');
  }
  return payload as T;
}
