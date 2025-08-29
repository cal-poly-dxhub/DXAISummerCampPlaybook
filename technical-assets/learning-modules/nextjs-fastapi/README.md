# next-fastapi Setup Guide

This guide will help you set up and run both the frontend (Next.js) and backend (FastAPI) for local development.

---

## Prerequisites

- [Node.js](https://nodejs.org/) (v18 or newer recommended)
- [Python 3.9+](https://www.python.org/downloads/)
- [VS Code](https://code.visualstudio.com/)

---

## Frontend (Next.js)

1. **Install dependencies**

   Open a terminal and navigate to the `frontend` directory:

   ```sh
   cd frontend
   npm install
   ```

2. **Run the development server locally**

   ```sh
   npm run dev
   ```

   The app will be available at [http://localhost:3000](http://localhost:3000).

## UI Components (shadcn/ui)

This project uses [shadcn/ui](https://ui.shadcn.com/) for reusable React components in the frontend.

- Components are located in `frontend/components/ui/`.
- To add or update components, see the [shadcn/ui docs](https://ui.shadcn.com/docs/components).
- Example usage:

  ```tsx
  import { Button } from "@/components/ui/button";
  ```

For more, visit the [shadcn/ui documentation](https://ui.shadcn.com/docs).

## Backend (FastAPI)

1. **Create a Python virtual environment using VS Code**

   - Open the `backend` folder in VS Code.
   - Open the Command Palette (`Cmd+Shift+P` on Mac, `Ctrl+Shift+P` on Windows/Linux).
   - Type and select `Python: Create Environment`.
   - Choose `Venv` and select your Python interpreter.
   - VS Code will create and activate a `.venv` folder.

2. **Install dependencies**

   In the VS Code terminal (with the `.venv` activated):

   ```sh
   pip install -r requirements.txt
   ```

3. **Run the FastAPI server locally with hot reload**

   ```sh
   uvicorn main:app --reload --port 8000
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000).

   - Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Usage

- The frontend will communicate with the backend at `http://localhost:8000`.
- Make sure both servers are running for full functionality.

---

## Troubleshooting

- If you have issues with Python environments, ensure VS Code is using the correct interpreter (bottom left corner).
- If ports are in use, stop other servers or change the port in the commands above.

---

## Project Structure

next-fastapi/
├── backend/ # FastAPI backend
│ ├── main.py
│ └── requirements.txt
└── frontend/ # Next.js frontend
