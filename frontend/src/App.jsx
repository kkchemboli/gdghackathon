import React from 'react'
import Navbar from './component/Navbar/navbar.jsx'
import { Routes, Route } from 'react-router-dom'
import Home from './pages/home/home.jsx'
import Video from './pages/video/video.jsx'
import Pdf from './pages/pdf/Pdf.jsx'
import { createBrowserRouter ,RouterProvider } from 'react-router-dom'

const App = () => {

  const router = createBrowserRouter([
    {
      path : "/",
      element: <><Navbar/><Home/></>,
    },
    {
      path : "/video",
      element: <><Navbar/><Video/></>,

    },
    
     {
      path: "/pdf",
      element: <><Navbar/><Pdf/></>
    },

    {
      path : "/video/:categoryId/:videoId",
      element: <><Navbar/><Pdf/></>,

    }
  ]);


  return (

    <RouterProvider router={router} />
  )
}

export default App