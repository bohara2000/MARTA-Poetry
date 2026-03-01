# MARTA-Poetry Frontend

React + Vite + Tailwind CSS frontend for the MARTA Poetry project.

## Quick Start

### Local Development

```bash
# Install dependencies
cd frontend
npm install

# Start dev server (runs on http://localhost:5173)
npm run dev

# Backend must be running on http://localhost:8000 for API calls to work
# See backend README for how to start the backend
```

### Build for Production

```bash
# Create optimized production build
npm run build

# Output goes to frontend/dist/

# Preview the build locally
npm run preview
```

## Environment Variables

Create `frontend/.env.local`:

```bash
# API Backend URL (default: http://localhost:8000)
VITE_API_URL=http://localhost:8000

# Enable debug logging
VITE_DEBUG=false
```

## Features

- **Route Selector**: Choose MARTA bus/train routes
- **Story Influence Slider**: Control randomness vs. narrative coherence
- **Context Options**: Time of day, passenger count, location
- **Audio Playback**: Listen to generated poems
- **Admin Panel**: Manage poetry graph, personalities, and themes
- **Real-time Updates**: Poem generation and graph modifications

## Deployment

### To Azure Static Web Apps

See [AZURE_DEPLOYMENT_GUIDE.md](../docs/AZURE_DEPLOYMENT_GUIDE.md#frontend-deployment) for complete instructions.

Quick version:

```bash
# Option 1: Automatic (GitHub Actions)
# Push to main → GitHub Actions builds and deploys automatically

# Option 2: Manual
bash ../scripts/deploy_frontend.sh
```

## Tech Stack

- **React 19**: UI framework
- **Vite**: Fast build tool
- **Tailwind CSS**: Styling
- **JavaScript ES6+**: Language

## Components

- `RouteSelector.jsx`: Choose transit route
- `StorySlider.jsx`: Control narrative influence
- `PoetryDisplay.jsx`: Show generated poems
- `AudioControls.jsx`: Play/pause audio
- `AdminPanel.jsx`: Admin interface
- `PersonalityManager.jsx`: Manage route personalities
- `ThemeManager.jsx`: Manage poetry themes
- `SystemStatus.jsx`: View graph health

## API Integration

The frontend calls the FastAPI backend at `/api/*` endpoints:

- `GET /api/routes` - List available MARTA routes
- `GET /api/poetry` - Generate a poem for a route
- `GET /api/routes/{route_id}` - Get route details
- Plus admin endpoints for management

API endpoint is dynamically determined by `src/utils/api.js`:
- Development: `http://localhost:8000`
- Production: Environment variable `VITE_API_URL` or same origin

## Troubleshooting

**"API calls failing / 404 errors"**
- Ensure backend is running on port 8000 (local dev)
- Check `VITE_API_URL` environment variable (production)
- Check CORS settings on backend

**"Page won't load / blank screen"**
- Check browser console for JavaScript errors
- Run `npm run build` to validate syntax
- Check that backend health endpoint responds

**"Build errors"**
- Run `npm install` again
- Delete `node_modules/` and `npm cache clean --force`
- Check Node.js version: `node --version` (16+ required)
