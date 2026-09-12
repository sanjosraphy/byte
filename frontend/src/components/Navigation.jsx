import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Menu,
  X,
  Home,
  MessageCircle,
  Lock,
  FileText,
  Zap,
  LogOut,
  ChevronRight,
} from 'lucide-react'
import { authAPI } from '../utils/api'
import './Navigation.css'

export default function Navigation() {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    authAPI.logout()
    navigate('/login')
  }

  const navItems = [
    { icon: Home, label: 'Dashboard', path: '/dashboard' },
    { icon: MessageCircle, label: 'Conversation', path: '/conversation' },
    { icon: Lock, label: 'Permissions', path: '/permissions' },
    { icon: FileText, label: 'Audit Logs', path: '/audit' },
    { icon: Zap, label: 'Demo', path: '/demo' },
  ]

  return (
    <>
      <nav className="navbar">
        <div className="navbar-container">
          <Link to="/dashboard" className="navbar-brand">
            <span className="brand-icon">⚡</span>
            <span className="brand-text">AI²</span>
          </Link>

          <button
            className="navbar-toggle"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>

          <div className={`navbar-menu ${isOpen ? 'open' : ''}`}>
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`navbar-item ${isActive ? 'active' : ''}`}
                  onClick={() => setIsOpen(false)}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  {isActive && <ChevronRight size={16} />}
                </Link>
              )
            })}

            <button className="navbar-logout" onClick={handleLogout}>
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </nav>
    </>
  )
}
