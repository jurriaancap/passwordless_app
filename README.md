# WebAuthn Passwordless Authentication

A FastAPI implementation of WebAuthn (Web Authentication) for passwordless authentication using biometrics, security keys, or platform authenticators.

## Features

- **Passwordless Registration** - Users register with biometrics/security keys
- **Passwordless Login** - Secure authentication without passwords
- **WebAuthn Standard** - Uses W3C WebAuthn specification
- **FastAPI Framework** - Modern, fast web framework
- **In-Memory Storage** - Simple development setup (not for production)

## Technology Stack

- **FastAPI** - Modern Python web framework
- **WebAuthn** - W3C Web Authentication standard
- **Python 3.12+** - Programming language
- **Uvicorn** - ASGI server

## Prerequisites

- Python 3.12 or higher
- A device with WebAuthn support (fingerprint reader, Face ID, security key, etc.)
- Modern browser with WebAuthn support (Chrome, Firefox, Safari, Edge)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd passwordless_auth
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the FastAPI server**
   ```bash
   python main.py
   ```

2. **Access the API**
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Registration Flow

1. **GET `/webauthn/register/options`**
   - Get registration challenge options
   - Query parameter: `email` (user's email)
   - Returns: WebAuthn credential creation options

2. **POST `/webauthn/register/verify`**
   - Verify registration response from authenticator
   - Body: `{"Email": "user@example.com", "credential": {...}}`
   - Returns: `{"status": "registered"}`

### Authentication Flow

3. **GET `/webautn/login/options`**
   - Get authentication challenge options
   - Query parameter: `email` (user's email)
   - Returns: WebAuthn credential request options

4. **POST `/webauth/login/verify`**
   - Verify authentication response from authenticator
   - Body: `{"email": "user@example.com", "credential": {...}}`
   - Returns: `{"status": "ok", "user": "email", "login_time": timestamp}`

## How WebAuthn Works

### Registration Process
1. User provides email
2. Server generates challenge and user ID
3. Browser calls WebAuthn API with challenge
4. User authenticates with biometrics/security key
5. Browser sends cryptographic credential to server
6. Server verifies and stores public key

### Login Process
1. User provides email
2. Server generates authentication challenge
3. Browser calls WebAuthn API with stored credentials
4. User authenticates with same method as registration
5. Browser sends signed challenge response
6. Server verifies signature with stored public key

## Development vs Production

### Current Setup (Development)
- **In-memory storage** - Data lost on restart
- **HTTP localhost** - Works for development
- **No rate limiting** - Simple development setup
- **Basic error handling** - Sufficient for testing

### Production Requirements
```python
# Required changes for production:

# 1. Database storage
users = {}  # → PostgreSQL/MongoDB
challenges = {}  # → Redis/Database with TTL

# 2. HTTPS and proper domains
RP_ID = "localhost"  # → "yourdomain.com"
ORIGIN = "http://localhost:8000"  # → "https://yourdomain.com"

# 3. Environment variables
# Move sensitive config to .env files

# 4. Security enhancements
# - Rate limiting
# - Input validation
# - Proper logging
# - Error handling
```

## Testing

### Using the Built-in HTML Test Interface (Recommended)

The application includes a complete HTML test interface for easy WebAuthn testing:

1. **Start the server**
   ```bash
   python main.py
   ```

2. **Open the test interface**
   - Navigate to: http://localhost:8000
   - You'll be automatically redirected to the test interface

3. **Test the Registration Flow**
   - Enter an email address (default: `test@example.com`)
   - Click "Register with WebAuthn"
   - Follow your browser's prompts to use biometrics/security key
   - You should see "Registration successful!"

4. **Test the Login Flow**
   - Use the same email address
   - Click "Login with WebAuthn"
   - Authenticate with the same method used during registration
   - You should see "Login successful!" with timestamp

### Test Interface Features

- **Real WebAuthn Integration** - Uses actual browser WebAuthn APIs
- **Visual Feedback** - Success/error messages with clear status
- **Detailed Logging** - Browser console shows full request/response details
- **Base64URL Handling** - Proper credential encoding/decoding
- **Error Handling** - Descriptive error messages for troubleshooting

### Browser Console Debugging

Open browser developer tools (F12) to see detailed logs:
```javascript
// Registration flow logs
Registration options received: {...}
Credential created: {...}
Registration successful!

// Login flow logs
Authentication options received: {...}
Credential retrieved: {...}
Login successful!
```

### Supported Authenticators

- **Platform Authenticators**: Touch ID, Face ID, Windows Hello, fingerprint readers
- **Security Keys**: USB/NFC FIDO2 keys (YubiKey, etc.)
- **Cross-Platform**: Any FIDO2-compatible device

### How to test 

1. Go to http://localhost:8000/test.html
2. register a random email acount (for example test@test.com)
3. login using the same email acount
**Note**: Full WebAuthn flow requires a proper browser client with WebAuthn support

### Real Testing Requirements

- **Browser with WebAuthn** support
- **HTTPS** or localhost
- **Biometric device** or security key
- **JavaScript client** to handle WebAuthn API calls

## Project Structure

```
passwordless_auth/
├── main.py              # FastAPI application
├── static/              # Static files for test interface
│   ├── test.html       # WebAuthn test interface
│   └── index.html      # Redirect to test interface
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Common Issues

### "The operation is insecure"
- **Cause**: WebAuthn requires HTTPS or localhost
- **Solution**: Use https:// or ensure you're on localhost

### "No authenticator available"
- **Cause**: No biometric device or security key
- **Solution**: Use a device with fingerprint, Face ID, or USB security key

### Empty credential response
- **Cause**: WebAuthn requires proper browser integration
- **Solution**: Cannot test via Swagger UI, need JavaScript client

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational/development purposes. Add appropriate license for your use case.

## Resources

- [WebAuthn Guide](https://webauthn.guide/)
- [W3C WebAuthn Specification](https://www.w3.org/TR/webauthn-2/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python WebAuthn Library](https://github.com/duo-labs/py_webauthn)

## Quick Start Example

```bash
# 1. Install and run
pip install -r requirements.txt
python main.py

# 2. Register a user
curl "http://localhost:8000/webauthn/register/options?email=test@example.com"

# 3. Access API docs
open http://localhost:8000/docs
```

---

**Note**: This is a development/educational implementation. For production use, implement proper database storage, HTTPS, rate limiting, and security measures.
