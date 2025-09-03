import React from 'react';
import { createRoot } from 'react-dom/client';
import { ChatWidget } from './components/ChatWidget';
import './styles/ChatWidget.css';

const root = createRoot(document.getElementById('root')!);
root.render(
  <React.StrictMode>
    <ChatWidget position="fullscreen" />
  </React.StrictMode>
); 
