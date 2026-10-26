# SoundWave

SoundWave is a music-focused social messaging platform developed using Python, Flask, SQLite, Socket.IO and the Spotify Web API. The application combines real-time messaging with Spotify integration, allowing users to communicate with friends while sharing and viewing music listening activity.

## Features

### Account Management
- User registration and login system
- Session-based authentication
- Personal user profiles

### Real-Time Messaging
- One-to-one messaging between users
- Instant message updates using Flask-SocketIO
- Persistent message history stored in SQLite

### Spotify Integration
- Spotify OAuth authentication
- Recently played track tracking
- Top artist display
- Top track display
- Current listening activity updates

### Social Features
- Add other users as contacts
- View other users' profiles
- See what friends are currently listening to
- Discover friends' favourite artists and tracks

## Technologies Used

- Python
- Flask
- Flask-SocketIO
- SQLite
- Spotipy
- Spotify Web API
- HTML
- CSS
- Jinja2

## Database Design

The application uses SQLite to manage data across five tables:

- **Users** - Stores account information and current listening activity
- **Conversations** - Stores connections between users
- **Messages** - Stores chat history
- **Music** - Stores users' top artists
- **Songs** - Stores users' top tracks

## Spotify Setup

SoundWave uses the Spotify Web API to retrieve listening data.

To access full Spotify functionality, Spotify accounts must be registered within the application's Spotify Developer Dashboard while the application remains in development mode. Unregistered accounts may not be able to access features such as:

- Top artists
- Top tracks
- Recently played tracks
- Current listening activity

## Future Improvements

- Group chat functionality
- Friend request system
- Password hashing and improved security
- Playlist sharing
- Personalised music recommendations
- Profile customisation
- Notifications for new messages

## Learning Outcomes

This project demonstrates:

- Full-stack web development with Flask
- Database design and implementation using SQLite
- Real-time communication using WebSockets
- API integration with Spotify
- OAuth authentication
- Session management
- Backend software development principles

## Author

Lucian Adderley

University Computer Science Project
