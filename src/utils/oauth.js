/**
 * OAuth Helper Functions
 */

const BASE_URL = "https://api.hcmus.fit";

/**
 * Initialize Google OAuth
 */
export const initGoogleAuth = () => {
  return new Promise((resolve, reject) => {
    // Load Google API script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google API'));
    document.head.appendChild(script);
  });
};

/**
 * Handle Google Login
 */
export const handleGoogleLogin = async () => {
  try {
    console.log('🔵 Initializing Google Auth...');
    await initGoogleAuth();
    console.log('🔵 Google SDK loaded');
    
    return new Promise((resolve, reject) => {
      const CLIENT_ID = '201712406039-0dl6eud6ekaf65d9oo550mhren5h5isc.apps.googleusercontent.com';
      
      // Create temporary container for Google button
      const tempDiv = document.createElement('div');
      tempDiv.style.position = 'fixed';
      tempDiv.style.top = '-9999px';
      tempDiv.style.left = '-9999px';
      document.body.appendChild(tempDiv);
      
      console.log('🔵 Initializing Google Sign-In...');
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: async (response) => {
          try {
            console.log('🔵 Google callback received');
            document.body.removeChild(tempDiv);
            
            // Send token to backend
            const res = await fetch(`${BASE_URL}/api/auth/google`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ token: response.credential })
            });
            
            const data = await res.json();
            console.log('🔵 Backend response:', data);
            
            if (res.ok) {
              resolve(data);
            } else {
              reject(new Error(data.message || 'Google login failed'));
            }
          } catch (err) {
            console.error('❌ Google callback error:', err);
            reject(err);
          }
        }
      });
      
      // Render button and auto-click it
      console.log('🔵 Rendering Google button...');
      window.google.accounts.id.renderButton(tempDiv, {
        type: 'standard',
        size: 'large',
        text: 'signin_with',
        shape: 'rectangular',
      });
      
      // Auto-click the button after a short delay
      setTimeout(() => {
        const googleButton = tempDiv.querySelector('div[role="button"]');
        if (googleButton) {
          console.log('🔵 Clicking Google button...');
          googleButton.click();
        } else {
          console.error('❌ Google button not found');
          document.body.removeChild(tempDiv);
          reject(new Error('Failed to render Google Sign-In button'));
        }
      }, 100);
      
      // Timeout after 60 seconds
      setTimeout(() => {
        if (document.body.contains(tempDiv)) {
          document.body.removeChild(tempDiv);
          reject(new Error('Google Sign-In timeout'));
        }
      }, 60000);
    });
  } catch (error) {
    console.error('❌ Google OAuth initialization failed:', error);
    throw new Error('Google OAuth initialization failed: ' + error.message);
  }
};

/**
 * Initialize Facebook SDK
 */
export const initFacebookSDK = () => {
  return new Promise((resolve, reject) => {
    // Check if already initialized
    if (window.FB) {
      console.log('Facebook SDK already loaded');
      resolve();
      return;
    }

    // Load Facebook SDK
    window.fbAsyncInit = function() {
      console.log('Initializing Facebook SDK...');
      window.FB.init({
        appId: '1839809623305106',
        cookie: true,
        xfbml: true,
        version: 'v18.0'
      });
      console.log('Facebook SDK initialized');
      resolve();
    };

    // Load SDK script
    if (!document.getElementById('facebook-jssdk')) {
      console.log('Loading Facebook SDK script...');
      const script = document.createElement('script');
      script.id = 'facebook-jssdk';
      script.src = 'https://connect.facebook.net/en_US/sdk.js';
      script.async = true;
      script.defer = true;
      script.onerror = () => {
        console.error('Failed to load Facebook SDK');
        reject(new Error('Failed to load Facebook SDK'));
      };
      document.body.appendChild(script);
    } else {
      console.log('Facebook SDK script already exists');
      if (window.FB) {
        resolve();
      }
    }
  });
};

/**
 * Handle GitHub Login
 */
export const handleGithubLogin = () => {
  const GITHUB_CLIENT_ID = 'Ov23ctE7T96xTrp7hSqY';
  const REDIRECT_URI = window.location.origin + '/login';
  
  // GitHub OAuth flow - redirect to GitHub
  const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=user:email`;
  
  // Redirect to GitHub (not popup)
  window.location.href = githubAuthUrl;
  
  // Return empty promise (won't be used because of redirect)
  return new Promise(() => {});
};

/**
 * Handle Facebook Login (Deprecated - cần Business Verification)
 */
export const handleFacebookLogin = () => {
  return new Promise(async (resolve, reject) => {
    try {
      console.log('Starting Facebook login...');
      await initFacebookSDK();
      
      console.log('Facebook SDK ready, checking login status...');
      
      // Check if FB is available
      if (!window.FB) {
        console.error('Facebook SDK not available');
        reject(new Error('Facebook SDK not loaded'));
        return;
      }

      console.log('Calling FB.login...');
      window.FB.login((response) => {
        console.log('Facebook login response:', response);
        
        if (response.authResponse) {
          console.log('Facebook auth successful, sending to backend...');
          // Send access token to backend
          fetch(`${BASE_URL}/api/auth/facebook`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              accessToken: response.authResponse.accessToken 
            })
          })
          .then(res => res.json())
          .then(data => {
            console.log('Backend response:', data);
            if (data.token) {
              resolve(data);
            } else {
              reject(new Error(data.message || 'Facebook login failed'));
            }
          })
          .catch(err => {
            console.error('Backend error:', err);
            reject(err);
          });
        } else {
          console.log('Facebook login cancelled or failed');
          reject(new Error('Facebook login cancelled'));
        }
      }, { scope: 'public_profile,email' });
    } catch (error) {
      console.error('Facebook login error:', error);
      reject(new Error('Facebook OAuth initialization failed: ' + error.message));
    }
  });
};
