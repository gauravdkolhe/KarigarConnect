import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import type { InAppNotification } from '../types';
import { api } from '../services/api';
import {
  Bell,
  Box,
  FileText,
  LogOut,
  MessageSquare,
  PlusCircle,
  Shield,
  Sparkles,
  User,
} from 'lucide-react';

interface NavbarProps {
  currentView: string;
  onNavigate: (view: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onNavigate }) => {
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState<InAppNotification[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);

  useEffect(() => {
    if (user) {
      loadNotifications();
      const interval = setInterval(loadNotifications, 30000); // 30s poll
      return () => clearInterval(interval);
    }
  }, [user]);

  const loadNotifications = async () => {
    try {
      const res = await api.listNotifications();
      setNotifications(res.notifications || []);
    } catch {
      // quiet fail
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      // quiet fail
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div
            className="brand"
            onClick={() => onNavigate('home')}
            style={{ cursor: 'pointer' }}
          >
            <Sparkles size={24} color="var(--color-primary)" />
            <span>KarigarConnect</span>
            {user && (
              <span className="brand-badge">
                {user.role.toUpperCase()}
              </span>
            )}
          </div>

          {/* Navigation Links by Role */}
          {user && (
            <div className="nav-links">
              {user.role === 'artisan' && (
                <>
                  <button
                    className={`nav-link ${currentView === 'artisan-dashboard' ? 'active' : ''}`}
                    onClick={() => onNavigate('artisan-dashboard')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    <Box size={18} />
                    <span>My Products</span>
                  </button>
                  <button
                    className={`nav-link ${currentView === 'workflow-new' ? 'active' : ''}`}
                    onClick={() => onNavigate('workflow-new')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    <PlusCircle size={18} />
                    <span>Add Craft</span>
                  </button>
                  <button
                    className={`nav-link ${currentView === 'inquiries' ? 'active' : ''}`}
                    onClick={() => onNavigate('inquiries')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    <MessageSquare size={18} />
                    <span>Inquiries</span>
                  </button>
                </>
              )}

              {user.role === 'buyer' && (
                <>
                  <button
                    className={`nav-link ${currentView === 'buyer-dashboard' ? 'active' : ''}`}
                    onClick={() => onNavigate('buyer-dashboard')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    <FileText size={18} />
                    <span>Sourcing Specs</span>
                  </button>
                  <button
                    className={`nav-link ${currentView === 'inquiries' ? 'active' : ''}`}
                    onClick={() => onNavigate('inquiries')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    <MessageSquare size={18} />
                    <span>My Inquiries</span>
                  </button>
                </>
              )}

              {user.role === 'admin' && (
                <button
                  className={`nav-link ${currentView === 'admin-dashboard' ? 'active' : ''}`}
                  onClick={() => onNavigate('admin-dashboard')}
                  style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  <Shield size={18} />
                  <span>Admin Oversight</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right Action Menu */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {user ? (
            <>
              {/* Notification Bell */}
              <div style={{ position: 'relative' }}>
                <button
                  onClick={() => setShowNotifs(!showNotifs)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    position: 'relative',
                    padding: '0.4rem',
                    color: 'var(--color-text-main)',
                  }}
                  title="Notifications"
                >
                  <Bell size={20} />
                  {unreadCount > 0 && (
                    <span
                      style={{
                        position: 'absolute',
                        top: 0,
                        right: 0,
                        background: 'var(--color-danger)',
                        color: 'white',
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        width: '16px',
                        height: '16px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {unreadCount}
                    </span>
                  )}
                </button>

                {showNotifs && (
                  <div
                    style={{
                      position: 'absolute',
                      right: 0,
                      top: '2.5rem',
                      width: '320px',
                      background: 'white',
                      borderRadius: 'var(--radius-lg)',
                      boxShadow: 'var(--shadow-lg)',
                      border: '1px solid var(--color-border)',
                      zIndex: 100,
                      padding: '1rem',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '0.75rem',
                        paddingBottom: '0.5rem',
                        borderBottom: '1px solid var(--color-border)',
                      }}
                    >
                      <h4 style={{ fontSize: '0.9rem', fontWeight: 700 }}>Notifications</h4>
                      {unreadCount > 0 && (
                        <button
                          onClick={handleMarkAllRead}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--color-primary)',
                            fontSize: '0.75rem',
                            cursor: 'pointer',
                            fontWeight: 600,
                          }}
                        >
                          Mark all read
                        </button>
                      )}
                    </div>

                    <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
                      {notifications.length === 0 ? (
                        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textAlign: 'center', padding: '1rem 0' }}>
                          No notifications yet.
                        </p>
                      ) : (
                        notifications.map((n) => (
                          <div
                            key={n.notification_id}
                            style={{
                              padding: '0.6rem',
                              borderRadius: 'var(--radius-sm)',
                              marginBottom: '0.4rem',
                              background: n.is_read ? 'transparent' : 'var(--color-primary-light)',
                              fontSize: '0.8rem',
                            }}
                          >
                            <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{n.title}</div>
                            <div style={{ color: 'var(--color-text-muted)', marginTop: '2px' }}>{n.message}</div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* User Profile Badge */}
              <button
                className="btn btn-outline btn-sm"
                onClick={() => onNavigate('profile')}
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <User size={15} />
                <span>{user.full_name}</span>
              </button>

              {/* Logout Button */}
              <button
                className="btn btn-outline btn-sm"
                onClick={() => {
                  logout();
                  onNavigate('home');
                }}
                title="Logout"
              >
                <LogOut size={15} />
              </button>
            </>
          ) : (
            <>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => onNavigate('login')}
              >
                Login
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => onNavigate('register')}
              >
                Get Started
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};
