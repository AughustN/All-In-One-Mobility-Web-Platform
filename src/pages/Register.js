import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Person, Lock, ArrowForward, Room } from '@material-ui/icons';
import { CircularProgress } from '@material-ui/core';
import { register } from '../api';
import OAuthButtons from '../components/OAuthButtons';
import '../css/Auth.css';
import vietnamMap from '../resource/vietnam.svg';

const Input = ({ label, icon, ...props }) => {
  return (
    <div className="space-y-1.5 w-full">
      <label style={{ fontSize: '0.75rem', fontWeight: 500, color: '#a1a1aa', letterSpacing: '0.05em', textTransform: 'uppercase', marginLeft: '0.25rem', display: 'block' }}>
        {label}
      </label>
      <div style={{ position: 'relative' }} className="group">
        {icon && (
          <div style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#71717a' }} className="group-focus-within:text-white">
            {icon}
          </div>
        )}
        <input
          {...props}
          style={{
            width: '100%',
            backgroundColor: 'rgba(24, 24, 27, 0.5)',
            border: '1px solid #27272a',
            color: 'white',
            fontSize: '0.875rem',
            borderRadius: '0.5rem',
            padding: '0.75rem',
            paddingLeft: icon ? '2.5rem' : '0.75rem',
            outline: 'none',
            transition: 'all 0.2s'
          }}
          onFocus={(e) => {
            e.target.style.borderColor = 'white';
            e.target.style.backgroundColor = '#18181b';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#27272a';
            e.target.style.backgroundColor = 'rgba(24, 24, 27, 0.5)';
          }}
        />
      </div>
    </div>
  );
};

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ username: '', password: '', confirmPassword: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      setError("Mật khẩu không khớp");
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await register(formData.username, formData.password);
      navigate('/login');
    } catch (err) {
      setError(err.message || 'Đăng ký thất bại');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      {/* Left Panel - Vietnam Map */}
      <div className="auth-left-panel">
        <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <div className="vietnam-map-container">
            <img src={vietnamMap} alt="Vietnam Map" />
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'white', marginTop: '-2rem', marginBottom: '0.5rem' }}>
            MAP APP HCMUS
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '1rem' }}>
            Khám phá bản đồ Việt Nam
          </p>
          
        </div>
         
      
      </div>

      {/* Right Panel - Register Form */}
      <div className="auth-right-panel">
        <div style={{ width: '100%', maxWidth: '400px' }}>
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
              <div style={{ height: '3rem', width: '3rem', backgroundColor: 'white', borderRadius: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 10px 15px -3px rgba(255, 255, 255, 0.1)' }}>
                <Room style={{ fontSize: '1.5rem', color: 'black' }} />
              </div>
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'white', letterSpacing: '-0.025em', marginBottom: '0.5rem' }}>
              Tạo tài khoản mới
            </h1>
            <p style={{ color: '#a1a1aa', fontSize: '0.875rem' }}>
              Tham gia cộng đồng bản đồ số Việt Nam
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.5)', borderRadius: '0.5rem', color: '#fca5a5', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input 
              label="Username" 
              name="username"
              placeholder="Nhập username" 
              type="text"
              required
              value={formData.username}
              onChange={handleChange}
              icon={<Person style={{ fontSize: '1rem' }} />}
            />
            
            <Input 
              label="Mật khẩu" 
              name="password"
              placeholder="••••••••" 
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              icon={<Lock style={{ fontSize: '1rem' }} />}
            />

            <Input 
              label="Xác nhận mật khẩu" 
              name="confirmPassword"
              placeholder="••••••••" 
              type="password"
              required
              value={formData.confirmPassword}
              onChange={handleChange}
              icon={<Lock style={{ fontSize: '1rem' }} />}
            />

            <button
              type="submit"
              disabled={isLoading}
              style={{
                width: '100%',
                backgroundColor: 'white',
                color: 'black',
                fontWeight: 600,
                height: '2.75rem',
                borderRadius: '0.5rem',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                marginTop: '0.5rem',
                border: 'none',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.7 : 1
              }}
              onMouseEnter={(e) => !isLoading && (e.target.style.backgroundColor = '#e4e4e7')}
              onMouseLeave={(e) => (e.target.style.backgroundColor = 'white')}
              className="group"
            >
              {isLoading ? (
                <CircularProgress size={20} style={{ color: 'black' }} />
              ) : (
                <>
                  Đăng Ký
                  <ArrowForward style={{ fontSize: '1rem' }} className="group-hover:translate-x-1" />
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div style={{ marginTop: '2rem', textAlign: 'center' }}>
            <p style={{ color: '#71717a', fontSize: '0.875rem' }}>
              Đã có tài khoản?{' '}
              <button 
                onClick={() => navigate('/login')}
                style={{
                  color: 'white',
                  fontWeight: 500,
                  marginLeft: '0.25rem',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  textDecorationColor: '#71717a',
                  textUnderlineOffset: '4px'
                }}
              >
                Đăng nhập
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
