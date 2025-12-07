# Bookworm API

### Overview
The Library Service API is a web-based system that allows tracking book inventory, managing users’ borrowings, and processing payments for borrowed books.


### Features
- **User Management:** Register new users and authenticate using JWT token.
- **Borrowing:** Take books to borrow, return them. 
- **Books:**
  - Admins: full CRUD for managing books.
  - Users: view and browse available books, see detailed information.
- **Payment:** Stripe checkout sessions for fines with webhook handling.
- **Notifications (Telegram):**
  - Notify admin about new borrowings.
  - Notify admin about successful payments.
  - Notify admin when a book is returned. 

### Technologies Used

- **Backend:** Django, Django REST Framework  
- **Authentication:** JWT 
- **Database:** PostgreSQL  
- **Payments:** Stripe API   
- **Notifications:** Telegram Bot API  
- **Containerization:** Docker, Docker Compose 

### How to run:
- Copy .env.sample -> .env and populate with required data 
- 'docker-compose up --build'
- Create admin user & create scheduled for running sync in DB
