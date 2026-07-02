import { createRoot } from 'react-dom/client';
import { App } from './App';
import './styles.css';

// OIDC authorization codes and SAML login tickets are single-use.  Do not wrap
// the root in StrictMode, which intentionally replays effects in development.
createRoot(document.getElementById('root')!).render(<App />);
