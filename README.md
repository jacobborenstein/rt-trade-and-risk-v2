# Real Time Equity Trading System

### Developed by:
- Yaakov Seif
- Yosef Bejman
- Jacob Borenstein
- Edmond Shrem
- Gabriel Loloey

## Overview

The **Equity Trading System** is a robust application designed for real-time trading activities, comprehensive trade capturing, position management, and real-time profit and loss (P&L) calculations. The system integrates multiple input mechanisms and delivers real-time updates, ensuring efficiency and scalability in trade management.

## Key Features

1. **Real-Time Trading Activities**: 
   - Capture trades from multiple sources and track in real-time.

2. **Position Management**:
   - View, manage, and aggregate trade positions efficiently.

3. **Real-Time Profit & Loss**:
   - Calculate and display profits and losses, updated in real-time.

4. **User Interface**:
   - Provides an easy-to-use dashboard for monitoring trades and positions, built using Streamlit.

## Technical Features

- **Fault-Tolerant**: Designed for high availability with load balancing.
- **Scalable**: Handles increased demand with a focus on performance and flexibility.
- **Transparency**: Ensures clear and accessible data for trade and risk assessments.

## System Architecture

The system is built using the following technologies:

- **Frontend**: Streamlit
- **Backend API**: FastAPI for real-time data handling and trade management
- **Database**: MongoDB for data persistence and Redis for caching and real-time data
- **Real-Time Data**: Finnhub API for real-time stock prices

### Components

- **Load Balancer**: Distributes requests to enhance system reliability and performance.
- **Authentication**: FastAPI-based authentication using JWT and password hashing (auth.py).
- **Main API**: FastAPI-powered API for user and trade management (main.py).
- **Position Aggregation**: Aggregates trades into positions and publishes results to Redis (position_agg.py).
- **Risk Calculator**: Calculates various risk metrics, including Sharpe ratio, Alpha, Beta, and more.
- **P&L Service**: Computes both realized and unrealized profits and losses, combining Redis and MongoDB data.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/equity-trading-system.git
   ```

2. Set up the environment:
   ```bash
   cd equity-trading-system
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up **MongoDB** and **Redis**.

5. Run the system with:
   ```bash
   streamlit run streamlit_main.py
   ```

## Running with Docker

1. Build the Docker image:
   ```bash
   docker build -t equity-trading-system .
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up
   ```

## Features in Development

- EC2 integration with NGINX for production deployment.
- Enhanced user interface for a smoother trading experience.
- Further optimization of system speed for faster updates.

## What We Learned

- **Technical**: Scaling architectures, using Singleton processes, and differentiating between caching (Redis) and persistence (MongoDB).
- **Business**: Components of an equity trading system, managing trades and positions.
- **Teamwork**: Collaborating in teams using pair programming, debugging, and coordinating work.
