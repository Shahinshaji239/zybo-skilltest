# Real-Time Individual Chat Application

A Django-based real-time chat application strictly following the MVT architecture, utilizing Django Channels for WebSocket communication, and built using Python, SQLite, HTML, CSS, JavaScript, and Bootstrap.

## Features Completed
- Custom User Model (email, username, password, is_online, last_seen)
- Authentication (Register, Login, Logout)
- User Dashboard listing all other registered users with their real-time online status.
- Real-Time Private Chat using WebSockets.
- Read Receipts (✓ for sent, ✓✓ for read).
- Prevents empty messages and auto-scrolls.

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd chat_project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\Activate.ps1
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install django channels daphne
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   ```





## Tech Stack
- **Backend:** Python, Django
- **WebSockets:** Django Channels, Daphne, InMemoryChannelLayer
- **Database:** SQLite
- **Frontend:** HTML, Vanilla CSS, Vanilla JavaScript, Bootstrap 5
