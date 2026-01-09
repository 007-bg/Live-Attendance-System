# Live Attendance System

A real-time attendance tracking system built with Django, Django Channels, and WebSockets. This system enables teachers to conduct live attendance sessions while students can check their attendance status in real-time.

## 🚀 Features

### Authentication & Authorization

- JWT-based authentication for secure API access
- Role-based access control (Admin, Teacher, Student)
- WebSocket authentication using JWT tokens
- User signup and login endpoints

### Class Management

- Teachers can create and manage classes
- Add students to classes
- View class details with student lists
- List all classes based on user role
- Retrieve classes by name

### Real-Time Attendance

- **Live attendance sessions** using WebSockets
- Teachers can start attendance sessions for their classes
- Real-time attendance marking (present/absent)
- Students can check their own attendance status in real-time
- Live attendance summaries with present/absent counts
- Session persistence to database
- Support for multiple concurrent class sessions

### Attendance History

- Complete attendance history for each class
- Session-based attendance records
- Detailed attendance reports with statistics

## 🛠️ Technology Stack

### Backend

- **Django 6.0.1** - Web framework
- **Django REST Framework** - API development
- **Django Channels 4.x** - WebSocket support
- **Redis** - Session storage and channel layer
- **MS SQL Server** - Primary database
- **drf-spectacular** - API documentation (Swagger/ReDoc)

### Authentication

- **djangorestframework-simplejwt** - JWT authentication
- **python-decouple** - Environment variable management

### Real-Time Communication

- **WebSockets** - Bi-directional real-time communication
- **Redis** - Message broker and session storage
- **Daphne** - ASGI server

## 📋 Prerequisites

- Python 3.12+
- Redis Server (running on localhost:6379)
- MS SQL Server
- ODBC Driver 17 for SQL Server
- Pipenv (for dependency management)

## 🔧 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/007-bg/Live-Attendance-System.git
   cd Live-Attendance-System
   ```

2. **Install dependencies**

   ```bash
   pipenv install
   ```

3. **Set up environment variables**

   Create a `.env` file in the project root:

   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   DB_ENGINE=mssql
   DB_NAME=AttendanceDB
   DB_HOST=localhost
   DB_DRIVER=ODBC Driver 17 for SQL Server
   DB_OPTIONS=TrustServerCertificate=yes;Trusted_Connection=yes
   ```

4. **Start Redis server**

   ```bash
   redis-server
   ```

5. **Run database migrations**

   ```bash
   pipenv run python manage.py migrate
   ```

6. **Create a superuser (optional)**

   ```bash
   pipenv run python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   pipenv run python manage.py runserver
   ```

The server will start at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 🔐 Authentication

### Get JWT Token

```http
POST /api/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Use Token in API Requests

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## 📡 WebSocket Connection

### Connect to WebSocket

```javascript
const token = "your_jwt_access_token";
const ws = new WebSocket(`ws://localhost:8000/ws/?token=${token}`);

ws.onopen = () => {
  console.log("Connected to WebSocket");
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Received:", message);
};
```

### WebSocket Events

#### 1. Mark Attendance (Teacher only)

```json
{
  "event": "ATTENDANCE_MARKED",
  "data": {
    "classId": "1",
    "studentId": "5",
    "status": "present"
  }
}
```

#### 2. Get Summary (Teacher only)

```json
{
  "event": "TODAY_SUMMARY",
  "data": {
    "classId": "1"
  }
}
```

#### 3. Check My Attendance (Student only)

```json
{
  "event": "MY_ATTENDANCE",
  "data": {
    "classId": "1"
  }
}
```

#### 4. End Session (Teacher only)

```json
{
  "event": "DONE",
  "data": {
    "classId": "1"
  }
}
```

## 🌐 REST API Endpoints

### User Management

- `POST /api/auth/signup/` - Register new user
- `POST /api/auth/login/` - User login
- `GET /api/auth/me/` - Get current user info
- `GET /api/students/` - List all students (Teacher only)

### Class Management

- `GET /api/class/list_classes/` - List all classes (role-based)
- `POST /api/class/create_class/` - Create new class (Teacher only)
- `GET /api/class/get-class/:class_name/` - Get class details by name
- `POST /api/class/:id/add-student/:student_id/` - Add student to class (Teacher only)

### Attendance

- `POST /api/class/start-attendance/` - Start attendance session (Teacher only)
- `GET /api/class/:id/my-attendance/` - Get student's attendance (Student only)

## 🧪 Testing the WebSocket

A simple HTML/JavaScript frontend is provided for testing WebSocket connections:

1. Open `frontend/index.html` in your browser
2. Enter your JWT access token
3. Click "Connect to WebSocket"
4. Use the provided forms to test different events

## 🏗️ Project Structure

```
Live-Attendance-System/
├── attendance_system/          # Main project settings
│   ├── settings.py            # Django settings
│   ├── urls.py                # URL routing
│   ├── asgi.py                # ASGI configuration
│   └── middleware/            # Custom middleware
│       └── jwt_auth.py        # JWT WebSocket authentication
├── users/                     # User management app
│   ├── models.py              # User model with roles
│   ├── views.py               # Authentication views
│   └── serializers/           # User serializers
├── classes/                   # Class and attendance app
│   ├── models.py              # Class and Attendance models
│   ├── views.py               # Class management views
│   ├── consumers.py           # WebSocket consumer
│   ├── routing.py             # WebSocket URL routing
│   ├── redis_utils.py         # Redis session management
│   └── serializers/           # Class serializers
├── frontend/                  # Testing frontend
│   └── index.html             # WebSocket test interface
├── .env                       # Environment variables
├── .gitignore                 # Git ignore rules
├── Pipfile                    # Dependencies
└── manage.py                  # Django management script
```

## 🔑 User Roles

### Admin

- Full system access
- Can manage users and classes

### Teacher

- Create and manage classes
- Add students to their classes
- Start attendance sessions
- Mark student attendance
- View attendance reports

### Student

- View enrolled classes
- Check own attendance status in real-time
- View attendance history

## 📊 Attendance Workflow

1. **Teacher starts an attendance session** via REST API:

   ```http
   POST /api/class/start-attendance/
   ```

2. **Teacher connects to WebSocket** and marks attendance in real-time:

   ```json
   {
     "event": "ATTENDANCE_MARKED",
     "data": { "classId": "1", "studentId": "5", "status": "present" }
   }
   ```

3. **Students check their status** in real-time via WebSocket:

   ```json
   { "event": "MY_ATTENDANCE", "data": { "classId": "1" } }
   ```

4. **Teacher ends the session** - attendance is persisted to database:

   ```json
   { "event": "DONE", "data": { "classId": "1" } }
   ```

5. **View attendance history** via REST API:
   ```http
   GET /api/class/get-class/:class_name/
   ```

## 🔒 Security Features

- JWT-based authentication for both REST API and WebSockets
- Role-based access control enforced at endpoint level
- Password hashing using Django's built-in system
- CSRF protection
- SQL injection protection via Django ORM
- WebSocket authentication middleware

## 🐛 Troubleshooting

### Redis Connection Error

Ensure Redis is running:

```bash
redis-server
```

### Database Connection Error

- Verify MS SQL Server is running
- Check database credentials in `.env`
- Ensure ODBC Driver 17 is installed

### WebSocket Connection Refused

- Check that the server is running with ASGI (Daphne)
- Verify Redis is running (required for channel layers)
- Ensure JWT token is valid and not expired
