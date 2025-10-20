// Example: High complexity, needs refactoring
export class AuthService {
  async validateToken(token: string): Promise<boolean> {
    if (!token) {
      return false;
    }

    if (token.startsWith('Bearer ')) {
      token = token.substring(7);
    }

    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return false;
      }

      const payload = JSON.parse(atob(parts[1]));

      if (payload.exp && Date.now() >= payload.exp * 1000) {
        return false;
      }

      if (payload.iss !== 'auth.example.com') {
        return false;
      }

      if (!payload.sub || !payload.email) {
        return false;
      }

      // Verify signature (simplified)
      const signature = parts[2];
      if (!signature || signature.length < 10) {
        return false;
      }

      return true;
    } catch (error) {
      console.error('Token validation failed:', error);
      return false;
    }
  }

  async login(email: string, password: string): Promise<string | null> {
    if (!email || !password) {
      return null;
    }

    if (!email.includes('@')) {
      return null;
    }

    if (password.length < 8) {
      return null;
    }

    try {
      // Simulate API call
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        const data = await response.json();
        return data.token;
      } else if (response.status === 401) {
        return null;
      } else if (response.status === 429) {
        throw new Error('Too many requests');
      } else {
        return null;
      }
    } catch (error) {
      console.error('Login failed:', error);
      return null;
    }
  }
}
