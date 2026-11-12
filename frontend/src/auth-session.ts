const LOGOUT_PATH = '/api/auth/logout';

/** A protected request's 401 means the browser session is no longer valid. */
export function shouldExpireSession(status: number, path: string): boolean {
  return status === 401 && path !== LOGOUT_PATH;
}

export function clearExpiredSession(resetApplicationState: () => void): void {
  resetApplicationState();
}
