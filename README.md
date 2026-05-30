# 🎫 Ticket Booking System: Concurrency & Race Condition Lab

A Django-based REST API designed to expose, analyze, and solve critical database race conditions. This project demonstrates how multiple near-simultaneous requests can lead to "overselling" and provides industry-standard solutions using **Pessimistic** and **Optimistic** locking.

---

## 📖 Table of Contents
1. [Core Problem: The Race Condition](#-core-problem-the-race-condition)
2. [Project Architecture](#-project-architecture)
3. [Implemented Solutions](#-implemented-solutions)
4. [Tech Stack](#-tech-stack)
5. [Getting Started](#-getting-started)
6. [Running the Concurrency Test](#-running-the-concurrency-test)
7. [Understanding Results](#-understanding-results)

---

## 🚨 Core Problem: The Race Condition
In naive booking implementations, a "Read-Modify-Write" cycle is used. If 50 users attempt to book the last available seat at the same time:
1. They all **read** the database and see 29/30 seats filled.
2. They all **modify** the value to 30 in memory.
3. They all **write** 30 back to the database.

**Result**: You report "Success" to 50 people, but your database only records 30 bookings. This project visualizes this failure and fixes it.

---

## 🏗 Project Architecture
- **Django REST API**: Serves endpoints for booking.
- **PostgreSQL**: Handles relational data and row-level locking.
- **Docker & Docker Compose**: Orchestrates the environment with health checks and automated migrations/seeding.
- **Load Generator**: A Python threading script that simulates high-concurrency traffic.

---

## 💡 Implemented Solutions

### 1. Naive (Vulnerable)
- **Endpoint**: `/api/events/<id>/book_vulnerable/`
- **Logic**: Standard ORM `.get()` and `.save()`.
- **Result**: Data corruption under load.

### 2. Pessimistic Locking
- **Endpoint**: `/api/events/<id>/book_pessimistic/`
- **Logic**: Uses `select_for_update()` to lock the database row.
- **Guarantee**: Correctness via serialization. Other requests wait in a queue.

### 3. Optimistic Locking
- **Endpoint**: `/api/events/<id>/book_optimistic/`
- **Logic**: Uses a `version` field for a "Compare-and-Swap" update.
- **Result**: High performance, returns `409 Conflict` on race detection.

### 4. Side-Effect Safety (`on_commit`)
- **Endpoint**: `/api/events/<id>/book_pessimistic_fail/`
- **Logic**: Demonstrates that external actions (like logging/emails) registered with `transaction.on_commit()` do **not** fire if a transaction rolls back.

---

## 🛠 Tech Stack
- **Backend**: Django 4.2+
- **Database**: PostgreSQL 15
- **Concurrency**: Gunicorn (Multi-threaded)
- **Testing**: Python Threading & Requests

---

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Desktop installed and running.
- Python 3.10+ (for running the test script locally).

### 1. Start the System
```bash
docker-compose up --build
```
This command starts the database, applies migrations, and seeds a "Tech Conference 2024" event with 30 seats.

### 2. Verify Startup
Ensure the containers are healthy:
```bash
docker ps
```

---

## 🧪 Running the Concurrency Test
The project includes a sophisticated test script that hammers all three endpoints with 50 concurrent requests each.

1. **Install requirements**:
   ```bash
   pip install requests
   ```

2. **Execute the test**:
   ```bash
   python test_concurrency.py
   ```

---

## 📊 Understanding Results
After testing, a `results.json` file is generated in the root directory.

- **`vulnerable`**: Expect `successful_bookings > 30` while `total_seats_in_db` remains low. This proves users were lied to.
- **`pessimistic`**: Expect exactly 30 successful bookings. Correctness is 100%.
- **`optimistic`**: Expect exactly 30 or fewer successful bookings, with `conflict_failures` capturing the rejected races.

Check the **Docker Logs** to verify the `CONFIRMATION` messages:
```bash
docker logs ticket-booking-system-web-1
```
You will see that messages only appear for successful, committed transactions.
