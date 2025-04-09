# WebSocket Authentication Guidelines for IoTSphere

This document outlines the patterns and best practices for implementing WebSocket authentication in the IoTSphere platform, based on our testing and development work.

## Core Principles

1. **Accept First, Then Authenticate**: Always accept WebSocket connections before attempting authentication to allow proper handshake completion.
2. **Avoid Double-Accept**: Once a connection has been accepted in middleware, never call `accept()` again in endpoint functions.
3. **Early Fail**: Close unauthorized connections immediately with appropriate status codes.
4. **Test Tokens**: Support test tokens in development environments to facilitate TDD.
5. **Clear Logging**: Implement detailed logging to assist with debugging authentication issues.

## Authentication Flow

```
Client ─────> WebSocket Connection Request
                      │
                      ▼
              Accept Connection
                      │
                      ▼
          Extract Authentication Token
                      │
                      ▼
                Validate Token
                    ┌─┴─┐
                    │   │
                    ▼   ▼
                 Valid  Invalid
                    │      │
                    │      ▼
                    │   Close Connection
                    │   (WS_1008_POLICY_VIOLATION)
                    │
                    ▼
        Add User Info to WebSocket State
                    │
                    ▼
            Process WebSocket Messages
```

## Middleware Implementation Pattern

```python
@router.websocket("/ws/my-endpoint")
async def my_endpoint(websocket: WebSocket):
    """
    Handle the endpoint logic, assuming the connection is already accepted by middleware.
    """
    # DO NOT call websocket.accept() here - the middleware has already done it

    # Connection already accepted and authenticated in middleware
    logger.info(f"Handler running for endpoint: {websocket.url.path}")

    # Access user info from the WebSocket state
    user = websocket.state.user

    try:
        # Process messages
        while True:
            message = await websocket.receive_text()
            # Handle message...

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    finally:
        # Clean up resources if needed
```

## Test Token Format

For development and testing, use JWT tokens with the following pattern:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTAwMSIsInVzZXJuYW1lIjoidGVzdF91c2VyIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ0MDYwMDAwfQ.thisIsATestToken
```

The token has these properties:
- Header: `{"alg":"HS256","typ":"JWT"}`
- Payload: `{"user_id":"test-user-001","username":"test_user","role":"admin","exp":1744060000}`
- Signature: Replaced with the string `thisIsATestToken` for test environments

## Environment Variables

The following environment variables control authentication behavior:

- `APP_ENV`: Set to `development` to enable test token support
- `DEBUG_WEBSOCKET`: Set to `true` to bypass authentication (for testing only)

## Common Issues and Solutions

1. **403 Forbidden Errors**:
   - Ensure proper token format and extraction
   - Check that the token is being passed correctly (query param or header)
   - Verify that user roles have the required permissions

2. **Multiple Accept Calls**:
   - Verify endpoint code does not call `accept()` when using middleware
   - Exception: For endpoints without middleware, call `accept()`

3. **Connection Drops After Authentication**:
   - Ensure proper error handling
   - Check for exceptions in the handler code
   - Verify WebSocketManager properly tracks connections

## Testing Recommendations

1. Create dedicated test scripts for WebSocket endpoints
2. Test with and without authentication tokens
3. Test with valid and invalid tokens
4. Test role-based access control
5. Test reconnection behavior

## Integration with IoTSphere Platform

In line with IoTSphere's device-agnostic architecture, the WebSocket authentication should:

1. Be consistent across all device types
2. Support the layered architecture with core and device-specific APIs
3. Work seamlessly with the unified event processing pipeline
4. Maintain security while enabling testing in development environments

---

*This documentation is part of IoTSphere's commitment to Test-Driven Development (TDD) principles.*
