import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App  from './App.tsx'
import AuthProvider from './context/AuthContext.tsx'
import { ModalProvider } from './context/ModalContext.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ModalProvider>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </ModalProvider>
  </StrictMode>
)
