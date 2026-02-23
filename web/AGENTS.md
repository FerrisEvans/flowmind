# Web Module Documentation

## Overview

The Web module provides the frontend interface for the Flowmind platform using React and TypeScript. It currently implements a three-column layout shell with placeholder components. Core functionality (API integration, plan visualization, session management) is not yet implemented.

## Architecture

### Technology Stack

- **React 18**: Component-based UI framework
- **TypeScript**: Type-safe JavaScript development
- **Vite**: Fast build tool and development server
- **Zustand**: State management (declared as dependency, not yet used in code)
- **Axios**: HTTP client (declared as dependency, not yet used in code)

### Layout Structure

The application implements a static three-column layout (`views/Layout/ThreeColumnLayout.tsx`):

#### 1. Navigation Column (`views/Navigation/SessionList.tsx`)
- Renders a static sidebar with "Sessions" header, a "+ New" button, and a "Settings" button
- **Planned:** Conversation history, session switching, saved workflows

#### 2. Chat Panel Column (`views/ChatPanel/ChatInterface.tsx`)
- Renders a text input field and send button (no submit handler or API call wired up)
- **Planned:** Sending intent to backend, displaying conversation history, intent refinement

#### 3. Canvas Column (`views/Canvas/DynamicCanvas.tsx`)
- Renders an empty container div
- **Planned:** Visualizing generated business flows as directed graphs, draggable nodes, step inspection

## Components

### Core Views

#### ThreeColumnLayout (`views/Layout/ThreeColumnLayout.tsx`)
- Composes the three columns (Navigation, Canvas, ChatPanel) into a CSS-based layout
- No resizing, responsive behavior, or cross-column communication is implemented yet

#### ChatInterface (`views/ChatPanel/ChatInterface.tsx`)
- Contains a controlled text input (`useState`) and a send button
- No form submission logic or API integration yet

#### DynamicCanvas (`views/Canvas/DynamicCanvas.tsx`)
- Empty container component — no visualization logic yet

#### SessionList (`views/Navigation/SessionList.tsx`)
- Static UI shell — no session data or interaction logic yet

## State Management (Planned)

Zustand and Axios are declared as dependencies in `package.json` but are **not yet imported or used** in any component. Currently only React's built-in `useState` is used (in ChatInterface for the input field).

### Planned Application State
- User intent input
- Generated plan and validation results
- Active session information
- UI layout states (column widths, visibility)

### Planned Data Flow
1. **Intent Input:** User enters business intent in ChatInterface
2. **API Communication:** Frontend sends intent to `/plan` endpoint
3. **Plan Visualization:** Response is processed and displayed in DynamicCanvas
4. **State Updates:** Zustand manages application state across components

## Integration Points (Planned)

### API Communication (not yet implemented)
- **POST `/plan`**: Will send user intent and receive structured plan
- **GET `/health`**: Will monitor backend service availability
- Vite dev server proxy is configured (`/api` → `localhost:8000`)

## Development Guidelines

### Component Standards
- Use TypeScript interfaces for all props and state
- Implement proper error boundaries
- Follow React best practices for performance
- Maintain consistent styling approach

### State Management
- Use Zustand for global application state
- Component-specific state for UI controls
- Proper cleanup of subscriptions and listeners

### UI/UX Principles
- Intuitive visualization of complex workflow dependencies
- Clear indication of validation errors or plan issues
- Smooth animations for interactions
- Accessibility compliance
