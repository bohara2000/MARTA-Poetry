import React, { useState } from 'react';
import PersonalityManager from './PersonalityManager';
import NarrativeManager from './NarrativeManager';
import PoemManager from './PoemManager';
import ThemeManager from './ThemeManager';
import SystemStatus from './SystemStatus';
import NarrativeAdherenceTest from './NarrativeAdherenceTest';

const AdminPanel = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('poems');

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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">MARTA Poetry Admin</h1>
              <p className="text-sm text-gray-600">Manage poems, narratives, and route personalities</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={onClose}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
              >
                ← Back to App
              </button>
              <span className="text-sm text-gray-500">
                🟢 Connected to Backend
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
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