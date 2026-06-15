# 📡 Social Media Post API

A full-featured social media REST API built with **FastAPI** and **PostgreSQL**, developed as the final project for **PROG315 – Object-Oriented Programming 2** at Limkokwing University of Creative Technology, Sierra Leone.

> Aligned with **UN SDG 9** (Industry, Innovation & Infrastructure) and the **Digital Public Goods** compliance framework.

---

## ✨ Features

- 🔐 **Authentication & Security** — OAuth2 Password Flow with JWT access tokens; bcrypt password hashing
- 📰 **Global Feed** — Paginated feed of all posts, ordered chronologically
- 📝 **Posts** — Full CRUD with ownership enforcement (403 on unauthorised edits)
- 💬 **Comments** — Threaded comments per post with owner-only edit/delete
- 🔔 **Notifications** — Mark individual or all notifications as read
- 👥 **Follow System** — Follow/unfollow users; view follower & following counts
- 🔍 **User Search** — Case-insensitive partial-match search by username or display name
- ⚡ **Async Handlers** — `async/await` on I/O-heavy endpoints (feed, notifications)
- 📄 **Auto Docs** — Interactive Swagger UI (`/docs`) and ReDoc (`/redoc`)

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| API Framework | FastAPI (Python) |
| Language | Python 3.11+ |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Authentication | OAuth2 + JWT (python-jose) |
| Password Hashing | Passlib (bcrypt) |
| ASGI Server | Uvicorn |
| Docs | Swagger UI & ReDoc (auto-generated) |
| Version Control | Git & GitHub |
| Licence | MIT |

---

## 📁 Project Structure

```
├── main.py          # App entry point; registers all routers
├── database.py      # SQLAlchemy engine, session factory, get_db dependency
├── models.py        # ORM models: User, Post, Comment, Follow, Notification
├── schemas.py       # Pydantic request/response schemas
├── auth.py          # JWT creation/verification, get_current_user dependency
├── routers/
│   ├── auth.py
│   ├── users.py
│   ├── posts.py
│   ├── comments.py
│   ├── notifications.py
│   └── follow.py
├── .env.example     # Environment variable template
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (running locally or via a hosted service)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in your values (see below)

# 5. Start the development server
uvicorn main:app --reload
```

### Environment Variables

Create a `.env` file in the project root with the following keys:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/socialmedia_db
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### Accessing the API Docs

Once the server is running, open:

- **Swagger UI** → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc** → [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 API Endpoints

All protected endpoints require a `Bearer <token>` in the `Authorization` header, obtained from `POST /auth/login`.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/auth/signup` | Register a new user | ❌ |
| `POST` | `/auth/login` | Login and receive JWT | ❌ |
| `GET` | `/users/me` | Get your own profile | ✅ |
| `GET` | `/users/{user_id}` | Get a user's public profile | ✅ |
| `GET` | `/users/search` | Search users by name/username | ✅ |
| `POST` | `/users/{user_id}/follow` | Follow a user | ✅ |
| `DELETE` | `/users/{user_id}/unfollow` | Unfollow a user | ✅ |
| `GET` | `/users/{user_id}/followers` | List followers + count | ✅ |
| `GET` | `/users/{user_id}/following` | List following + count | ✅ |
| `GET` | `/feed` | Get paginated global feed | ✅ |
| `POST` | `/posts` | Create a post | ✅ |
| `GET` | `/posts/{post_id}` | Get a single post | ✅ |
| `PUT` | `/posts/{post_id}` | Edit a post (owner only) | ✅ |
| `DELETE` | `/posts/{post_id}` | Delete a post (owner only) | ✅ |
| `POST` | `/posts/{post_id}/comments` | Add a comment | ✅ |
| `GET` | `/posts/{post_id}/comments` | List comments on a post | ✅ |
| `PUT` | `/comments/{comment_id}` | Edit a comment (owner only) | ✅ |
| `DELETE` | `/comments/{comment_id}` | Delete a comment (owner only) | ✅ |
| `GET` | `/notifications` | List your notifications | ✅ |
| `PATCH` | `/notifications/{id}/read` | Mark one notification as read | ✅ |
| `PATCH` | `/notifications/read-all` | Mark all notifications as read | ✅ |

---

## 🗄️ Database Schema

```
User ──< Post ──< Comment
 │
 ├──< Notification
 │
 └──< Follow (self-referential many-to-many)
       follower_id ──> User.id
       followed_id ──> User.id
```

Tables are created automatically by SQLAlchemy on application startup.

---

## 🔒 Security

- Passwords are hashed with **bcrypt** (via Passlib) — plain-text passwords are never stored
- JWT tokens are signed with a secret key and expire after the configured time window
- Resource ownership is enforced on all edit/delete operations — a mismatch returns `403 Forbidden`
- Sensitive config (DB credentials, JWT secret) lives in `.env` and is excluded from version control

---

## 🌍 SDG Alignment

This project is aligned with the **UN Sustainable Development Goals**:

| SDG | Relevance |
|---|---|
| **SDG 9** – Industry, Innovation & Infrastructure | Demonstrates locally built open-source digital infrastructure in Sierra Leone |
| **SDG 4** – Quality Education | Builds in-demand software development skills among Sierra Leonean students |
| **SDG 17** – Partnerships for the Goals | Open-source MIT licence enables reuse and extension by other developers |

---

## 🚧 Future Enhancements

- [ ] Real-time notifications via WebSockets
- [ ] Like / reaction system for posts and comments
- [ ] Image & media uploads (cloud storage integration)
- [ ] Personalised feed (prioritise followed accounts)
- [ ] Redis caching and rate limiting
- [ ] Automated test suite with pytest + GitHub Actions CI
- [ ] Push notification support for mobile clients

---

## 👥 Group Members

| Name | Student ID | 
|---|---|---|
| [Tamba Richard Seddu] | [905005423] 
| [Ibrahim F.L Conteh] | [905005544] 
| [Rayyan Hurai Nyass] | [905004074] 

---

## 📄 Licence

This project is licensed under the **MIT Licence** — see the [LICENSE](LICENSE) file for details.

---

> **Module:** PROG315 – Object-Oriented Programming 2 | Limkokwing University of Creative Technology, Sierra Leone  
> **Semester:** 4 (March – July 2026) | **Examiner:** Amandus Benjamin Coker
