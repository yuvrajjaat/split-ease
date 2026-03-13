# SplitEase

A group expense splitting app that tracks shared expenses and simplifies debt settlement among friends. Built with Django REST Framework and React.

## Features

- **Expense Tracking** — Record shared expenses with multiple split modes: equal, exact amounts, percentage, or share-based
- **Smart Debt Simplification** — Uses a greedy algorithm to minimize the number of transactions needed to settle all debts
- **Automatic Netting** — Reverse debts are automatically offset to reduce clutter
- **Settle Up** — Partial or full debt settlement with real-time balance updates
- **Group Management** — Add/remove members and view per-person balances

## Tech Stack

| Layer    | Technology                     |
|----------|--------------------------------|
| Backend  | Django, Django REST Framework  |
| Frontend | React, Axios                   |
| Database | SQLite                         |

## Getting Started

### Prerequisites

- Python 3.x
- Node.js & npm

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

The app will open at `http://localhost:3000`.

## API Endpoints

| Method | Endpoint                       | Description                  |
|--------|--------------------------------|------------------------------|
| GET    | `/users`                       | List all users               |
| POST   | `/users`                       | Create a new user            |
| DELETE | `/users/<username>`            | Delete a user                |
| GET    | `/expenses`                    | List all expenses            |
| POST   | `/expenses`                    | Create a new expense         |
| PUT    | `/expenses/<id>`               | Edit an expense              |
| DELETE | `/expenses/<id>`               | Delete an expense            |
| GET    | `/debts`                       | List all pairwise debts      |
| GET    | `/optimisedDebts`              | List simplified debts        |
| POST   | `/debts/settle`                | Settle a debt                |

## Screenshots

<!-- Add screenshots here -->
