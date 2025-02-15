# Feature-Core
![Logo](frontend/src/assets/logo.png)

**Feature-Core** is a feature management system designed to help you manage feature flags with ease. It supports **parent-child relationships** between feature flags, allowing you to enable or disable features hierarchically. Built with **FastAPI** (backend) and **React** (frontend), Feature-Core is production-ready and easy to set up.

## Features
**1. Feature Flag Management**
- **Create**, **Update**, and **Delete** feature flags.
- Enable or disable feature flags with a simple toggle.
- **Parent-Child Relationships**: Define hierarchical relationships between feature flags.
    - If a parent feature is toggled, all its children are automatically updated.
    - Only **one level of nesting** is allowed (parent → child, no grandparent → parent → child).

**2. Real-Time Updates**
- Changes to feature flags are reflected in real-time across the application.
- **Auto-Propagation**: Toggling a parent feature automatically updates its children.

**3. User-Friendly UI**
- **Expandable Tree View**: View and manage parent-child relationships in a hierarchical tree structure.
- **Toggle Switches**: Easily enable or disable features with a toggle switch.
- **Edit Feature Names**: Update feature names directly from the UI.
- **Create New Features**: Add new feature flags with a simple form.
- **Delete Features**: Delete a feature flag with simple click.

**4. Scalable and Production-Ready**
- **FastAPI Backend**: High-performance API built with Python.
- **React Frontend**: Modern, responsive UI built with React and Material-UI.
- **Dockerized Setup**: Easy deployment with Docker and Docker Compose.

## Getting Started
**Prerequisites**
- Docker and Docker Compose installed on your machine

**Setup**
1. **Clone the Repository**:
```bash
git clone https://github.com/Vishal487/Feature-Core.git
cd feature-core
```
2. **Set Up Environment Variables**:
    - Update the `.env` file with your database credentials.
3. **Start the Application**:
```bash
docker-compose up -d
```
4. **Access the Application**:
    - **Frontend**: Open http://localhost:3000 in your browser.
    - **Backend API Docs**: Open http://localhost:8000/docs to explore the API.


## Usage
**1. Create a Feature Flag**
- Click the Create New Feature button (`+`) on the top-right corner.
- Fill in the feature name, toggle the switch to enable/disable, and select a parent feature (optional).
- Click Save.

**2. Toggle a Feature**
- Use the toggle switch next to each feature to enable or disable it.
- If the feature has children, a warning will appear.

**3. Edit a Feature Name**
- Simply click on the feature name to edit it.
- Update the name and click Save.

**4. View Parent-Child Relationships**
- Click the expand/collapse icon (`▼`) next to a parent feature to view its children.

**5. Delete a Feature**
- Delete a feature flag by clicking on the delete icon.
- A warning will appear.
- You can cancel or proceed.

## API Documentation
Explore the API endpoints using the **Swagger UI**:
- Open http://localhost:8000/docs in your browser.

## Key Endpoints
- **GET** `/features`: Get all feature flags.
- **POST** `/features`: Create a new feature flag.
- **PUT** `/features/{id}`: Update a feature flag.
- **DELETE** `/features/{id}`: Delete a feature flag.

## Development
### Running Locally

**1. Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
**2. Frontend**
```bash
cd frontend
npm install
npm start
```

### Testing
- Run unit tests for the backend:
```bash
cd backend
pytest
```
