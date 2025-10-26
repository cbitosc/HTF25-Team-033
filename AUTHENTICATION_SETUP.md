# DocuMind AI - Authentication Setup Guide

## 🚀 Quick Start with Authentication

This guide will help you set up user authentication and MongoDB integration for DocuMind AI.

## 📋 Prerequisites

1. **MongoDB**: Either local MongoDB or MongoDB Atlas account
2. **Python 3.11+**: For the backend
3. **Node.js 18+**: For the frontend

## 🔧 Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the `backend` directory:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
# For MongoDB Atlas: MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/

DATABASE_NAME=documind

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Optional: File upload settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
ALLOWED_FILE_TYPES=pdf,txt
```

### 3. Start the Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Frontend

```bash
npm run dev
```

## 🗄️ MongoDB Atlas Setup (Recommended)

### 1. Create MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free account
3. Create a new cluster (free tier available)

### 2. Get Connection String

1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string
4. Replace `<password>` with your database user password
5. Update `MONGODB_URL` in your `.env` file

### 3. Database User Setup

1. Go to "Database Access" in Atlas
2. Add a new database user
3. Set username and password
4. Grant "Read and write to any database" permissions

## 🔐 Authentication Features

### ✅ Implemented Features

- **User Registration**: Create new accounts with email and password
- **User Login**: Secure JWT-based authentication
- **Password Hashing**: Bcrypt encryption for security
- **Protected Routes**: All document operations require authentication
- **User Sessions**: Persistent login across browser sessions
- **Logout**: Secure token invalidation

### 🎯 User Experience

- **Beautiful UI**: Modern, responsive authentication pages
- **Form Validation**: Real-time validation and error handling
- **Loading States**: Smooth loading indicators
- **Error Handling**: Clear error messages
- **Auto-redirect**: Automatic navigation after login/signup

## 📊 Database Collections

The system automatically creates these collections:

### `users`
- Stores user account information
- Indexed by email for fast lookups
- Includes password hashes and metadata

### `documents`
- Stores document metadata per user
- Indexed by user_id and upload_time
- Links to file storage and embeddings

### `chat_history`
- Stores chat conversations per user/document combination
- Enables persistent chat history across sessions
- Indexed for efficient querying

## 🔒 Security Features

- **JWT Tokens**: Secure, stateless authentication
- **Password Hashing**: Bcrypt with salt rounds
- **CORS Protection**: Configured for your domain
- **Input Validation**: Pydantic models for data validation
- **SQL Injection Protection**: MongoDB with proper querying
- **Token Expiration**: Configurable token lifetime

## 🚀 Production Deployment

### Environment Variables for Production

```env
# Use strong, unique secret key
SECRET_KEY=your-production-secret-key-here

# MongoDB Atlas connection
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/

# Production database name
DATABASE_NAME=documind_production

# Optional: Enable HTTPS
HTTPS_ENABLED=true
```

### Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use MongoDB Atlas (not local MongoDB)
- [ ] Enable HTTPS in production
- [ ] Set up proper CORS origins
- [ ] Configure file upload limits
- [ ] Set up monitoring and logging

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check your connection string
   - Verify network access in MongoDB Atlas
   - Ensure database user has proper permissions

2. **Authentication Errors**
   - Verify SECRET_KEY is set
   - Check JWT token expiration settings
   - Ensure frontend and backend are on same domain

3. **File Upload Issues**
   - Check file size limits
   - Verify file type restrictions
   - Ensure uploads directory exists

## 📈 Next Steps

- **Email Verification**: Add email confirmation for new accounts
- **Password Reset**: Implement forgot password functionality
- **Social Login**: Add Google/GitHub OAuth
- **User Profiles**: Allow users to update their information
- **Admin Panel**: Create admin interface for user management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Happy coding! 🎉**
