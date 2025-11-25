// Token Manager - Handle token expiration gracefully

let isLoggingOut = false;

export function handleTokenExpiration() {
  if (isLoggingOut) return; // Prevent multiple logout calls
  
  isLoggingOut = true;
  
  console.warn('Session expired. Logging out...');
  
  // Clear auth data
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  
  // Dispatch auth change event
  window.dispatchEvent(new Event('auth-change'));
  
  // Show user-friendly message
  const message = 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
  
  // Create a temporary notification
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 70px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #ffffffff 0%, #0a0a0aff 100%);
    color: white;
    padding: 16px 24px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    z-index: 10000;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
    font-weight: 500;
    animation: slideDown 0.3s ease-out;
  `;
  notification.textContent = message;
  
  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideDown {
      from {
        opacity: 0;
        transform: translateX(-50%) translateY(-20px);
      }
      to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
      }
    }
  `;
  document.head.appendChild(style);
  document.body.appendChild(notification);
  
  // Remove notification after 3 seconds
  setTimeout(() => {
    notification.style.animation = 'slideDown 0.3s ease-out reverse';
    setTimeout(() => {
      document.body.removeChild(notification);
      document.head.removeChild(style);
    }, 300);
  }, 3000);
  
  // Redirect to login after a short delay
  setTimeout(() => {
    window.location.href = '/login';
    isLoggingOut = false;
  }, 1000);
}

export function isTokenValid() {
  const token = localStorage.getItem('token');
  return !!token;
}

export function getToken() {
  return localStorage.getItem('token');
}

export function setToken(token) {
  localStorage.setItem('token', token);
}

export function clearToken() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
}
