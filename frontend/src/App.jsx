import React from 'react'
import Navbar from './component/Navbar/navbar.jsx'
import { Routes, Route } from 'react-router-dom'
import Home from './src/pages/home/home.js'
import Video from './src/pages/video/video.js'
import Pdf from './src/pages/pdf/Pdf.js'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'

const App = () => {

  const router = createBrowserRouter([
    {
      path: "/",
      element: <><Navbar /><Home /></>,
    },
    {
      path: "/video",
      element: <><Navbar /><Video /></>,

    },
    {
      path: "/video/:categoryId/:videoId",
      element: <><Navbar /><Pdf /></>,

    }
  ]);


  return (

    <RouterProvider router={router} />
  )
}

export default App