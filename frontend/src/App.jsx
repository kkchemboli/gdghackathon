import React from 'react';
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';
import Navbar from './component/Navbar/navbar.jsx';
import Home from './pages/home/home.jsx';
import Video from './pages/video/video.jsx';
import Pdf from './pages/pdf/Pdf.jsx';
import LoginPage from './LoginPage';
import ProtectedRoute from './ProtectedRoute';
import { useAuth } from './AuthContext';

const AppLayout = () => {
  const { isAuthenticated } = useAuth();
  return (
    <>
      {isAuthenticated && <Navbar />}
      <Outlet />
    </>
  );
};

const App = () => {
  const router = createBrowserRouter([
    {
      path: '/',
      element: <AppLayout />,
      children: [
        {
          path: 'login',
          element: <LoginPage />,
        },
        {
          path: '/',
          element: <ProtectedRoute />,
          children: [
            {
              path: '/',
              element: <Home />,
            },
            {
              path: 'video',
              element: <Video />,
            },
            {
              path: 'pdf',
              element: <Pdf />,
            },
            {
              path: 'video/:categoryId/:videoId',
              element: <Pdf />,
            },
          ],
        },
      ],
    },
  ]);

  return <RouterProvider router={router} />;
};

export default App;
