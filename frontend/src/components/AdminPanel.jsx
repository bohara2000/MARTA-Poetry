import React, { useState } from 'react';
import PersonalityManager from './PersonalityManager';
import NarrativeManager from './NarrativeManager';
import PoemManager from './PoemManager';
import ThemeManager from './ThemeManager';
import SystemStatus from './SystemStatus';
import NarrativeAdherenceTest from './NarrativeAdherenceTest';

const AdminPanel = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('poems');
  const [menuOpen, setMenuOpen] = useState(false);

  const tabs = [
    { id: 'poems', label: 'Poem Management', icon: '📝' },
    { id: 'narratives', label: 'Narrative Structure', icon: '📖' },
    { id: 'themes', label: 'Theme Management', icon: '🏷️' },
    { id: 'personalities', label: 'Route Personalities', icon: '🎭' },
    { id: 'testing', label: 'Narrative Testing', icon: '🧪' },
    { id: 'system', label: 'System Status', icon: '⚙️' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Admin Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8">
          <div className="flex justify-between items-center py-3 sm:py-4">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">MARTA Poetry Admin</h1>
              <p className="text-xs sm:text-sm text-gray-600 hidden sm:block">Manage poems, narratives, and route personalities</p>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <button
                onClick={onClose}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-xs sm:text-sm"
              >
                ← <span className="hidden sm:inline">Back to App</span>
              </button>
              <span className="text-xs sm:text-sm text-gray-500 hidden sm:inline">
                🟢 Connected
              </span>
              
              {/* Hamburger Menu */}
              <div className="relative">
                <button
                  onClick={() => setMenuOpen(!menuOpen)}
                  className="p-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                  aria-label="Navigation menu"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
                
                {menuOpen && (
                  <>
                    {/* Backdrop */}
                    <div 
                      className="fixed inset-0 z-10" 
                      onClick={() => setMenuOpen(false)}
                    />
                    
                    {/* Dropdown Menu */}
                    <div className="absolute right-0 mt-2 w-56 rounded-lg shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
                      <div className="py-1" role="menu">
                        {tabs.map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => {
                              setActiveTab(tab.id);
                              setMenuOpen(false);
                            }}
                            className={`${
                              activeTab === tab.id
                                ? 'bg-blue-50 text-blue-700'
                                : 'text-gray-700 hover:bg-gray-100'
                            } w-full text-left px-4 py-3 text-sm flex items-center space-x-3`}
                            role="menuitem"
                          >
                            <span className="text-lg">{tab.icon}</span>
                            <span className="font-medium">{tab.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-3 sm:py-6">
        {activeTab === 'poems' && <PoemManager />}
        {activeTab === 'narratives' && <NarrativeManager />}
        {activeTab === 'themes' && <ThemeManager />}
        {activeTab === 'personalities' && <PersonalityManager />}
        {activeTab === 'testing' && <NarrativeAdherenceTest />}
        {activeTab === 'system' && <SystemStatus />}
      </div>
    </div>
  );
};

export default AdminPanel;