import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from './AuthContext';
import api from './api';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import Navbar from './components/Navbar';
import HeroSection from './components/HeroSection';

const LoginPage = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/'); // Redirect if already authenticated
    }
  }, [isAuthenticated, navigate]);

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const response = await api.post('/auth/google', {
          credential: tokenResponse.access_token, // Sending access token as credential
        });
        const { access_token } = response.data;
        login(access_token);
      } catch (error) {
        console.error('Login Failed:', error);
      }
    },
    onError: () => {
      console.log('Login Failed');
    }
  });

  return (
    <div className="min-h-screen bg-background selection:bg-primary/20">
      <Navbar onLogin={() => googleLogin()} />
      <HeroSection />
    </div>
  );
};

export default LoginPage;
