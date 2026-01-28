import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { useAuth } from './AuthContext';
import api from './api';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

const LoginPage = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/'); // Redirect if already authenticated
    }
  }, [isAuthenticated, navigate]);

  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    try {
      const response = await api.post('/auth/google', {
        credential: credentialResponse.credential,
      });
      const { access_token } = response.data;
      login(access_token);
      // The useEffect will now handle the redirect
    } catch (error) {
      console.error('Login Failed:', error);
    }
  };

  const handleError = () => {
    console.log('Login Failed');
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={handleError}
      />
    </div>
  );
};

export default LoginPage;
