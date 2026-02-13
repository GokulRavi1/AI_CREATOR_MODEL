# AI Character Studio (React Frontend)

This is the new React-based frontend for the AI Character Studio.

## Setup

1.  Install dependencies:
    ```bash
    npm install
    ```

2.  Run development server:
    ```bash
    npm run dev
    ```
    This will start the frontend on `http://localhost:5173`.
    It proxies `/api` requests to the backend at `http://127.0.0.1:8000`.

## Architecture

-   **Framework**: React + Vite
-   **Styling**: Vanilla CSS (Premium Dark Theme) + Lucide Icons
-   **State Management**: Context API (`AppContext`)
-   **Data Fetching**: Axios (`api.js`)

## Migration Status

-   [x] Project Setup
-   [x] Layout & Sidebar
-   [x] Identity Lab (Face Discovery, Body Consistency)
-   [x] Content Studio (Canvas, ControlNet)
