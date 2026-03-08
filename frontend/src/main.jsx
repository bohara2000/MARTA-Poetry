import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import RadioPage from './RadioPage.jsx'

const Root = window.location.pathname === '/radio' ? RadioPage : App;

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
