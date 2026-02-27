# Ticket Show — User Flows

Complete map of every user flow across the microservices platform.

---

## 1. Authentication

### 1a. Register

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant Auth as Auth Service
    participant DB as Auth DB

    U->>GW: POST /auth/register
    GW->>Auth: proxy
    Auth->>DB: INSERT user + wallet (balance 0)
    DB-->>Auth: user created
    Auth-->>GW: UserResponse
    GW-->>U: 201 Created
```

### 1b. Login

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant Auth as Auth Service

    U->>GW: POST /auth/login
    GW->>Auth: proxy
    Auth->>Auth: verify password, generate JWT
    Auth-->>GW: access_token + token_type
    GW-->>U: 200 OK + JWT
```

### 1c. View Profile

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant Auth as Auth Service

    U->>GW: GET /auth/me [JWT]
    GW->>Auth: GET /auth/verify (validate token)
    GW->>Auth: GET /auth/me
    Auth-->>GW: UserResponse + wallet_balance
    GW-->>U: profile data
```

### 1d. View Wallet

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant Auth as Auth Service

    U->>GW: GET /auth/wallet [JWT]
    GW->>Auth: proxy
    Auth-->>GW: WalletResponse (balance + transactions)
    GW-->>U: wallet data
```

---

## 2. Browsing Shows & Venues

### 2a. Browse Dashboard (All Shows)

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant ES as Event Service
    participant S3 as MinIO

    U->>GW: GET /shows/?limit=20
    GW->>ES: proxy
    ES-->>GW: List of ShowResponse (incl. poster_url)
    GW-->>U: show cards
    U->>S3: GET poster_url (direct)
    S3-->>U: poster image
```

### 2b. Search Shows & Venues

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant SS as Search Service
    participant EL as Elasticsearch

    U->>GW: GET /search?q=interstellar&city=Mumbai
    GW->>SS: proxy
    SS->>EL: fuzzy full-text query
    EL-->>SS: matching shows + venues
    SS-->>GW: SearchResponse
    GW-->>U: results
```

### 2c. View Show Detail + Venues + Schedules

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant ES as Event Service

    U->>GW: GET /shows/{show_id}/venues?city=Mumbai
    GW->>ES: proxy
    ES-->>GW: venues showing this film

    U->>GW: GET /schedules/venue/{venue_id}?show_id=X
    GW->>ES: proxy
    ES-->>GW: showtimes list
    GW-->>U: showtimes for selection
```

### 2d. View Available Seats

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant BS as Booking Service

    U->>GW: GET /bookings/schedule/{schedule_id}/seats [JWT]
    GW->>BS: proxy (user_id from JWT)
    BS-->>GW: seat map (available / locked / booked)
    GW-->>U: interactive seat picker
```

---

## 3. Booking & Payment

### 3a. Create Booking, Pay, and Confirm

This is the most complex flow spanning 4 services + Kafka.

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant BS as Booking Service
    participant PS as Payment Service
    participant Dodo as Dodo Payments
    participant K as Kafka
    participant NS as Notification Service

    Note over U,NS: Step 1 — Create Booking
    U->>GW: POST /bookings { schedule_id, seat_ids }
    GW->>BS: proxy (user_id)
    BS->>BS: lock seats (row-level lock)
    BS->>BS: INSERT booking (status=PENDING)
    BS-->>GW: BookingResponse (PENDING)
    GW-->>U: booking created

    Note over U,NS: Step 2 — Initiate Payment
    U->>GW: POST /payments { booking_id, payment_method }
    GW->>PS: proxy
    PS->>PS: fetch booking from Booking Service
    PS->>PS: INSERT payment (status=PENDING)

    alt payment_method = DODO
        PS->>Dodo: create checkout session
        Dodo-->>PS: checkout_url
        PS-->>GW: PaymentResponse + checkout_url
        GW-->>U: redirect to Dodo checkout
    else payment_method = WALLET
        PS->>PS: INSERT payment (status=COMPLETED)
        PS->>BS: PATCH booking status to CONFIRMED
        PS->>K: publish booking.successful
        K->>NS: consume booking.successful
        NS->>NS: send confirmation email (SMTP)
        PS-->>GW: PaymentResponse (COMPLETED)
        GW-->>U: payment confirmed
    end

    Note over U,NS: Step 3 — Dodo Webhook (async, external)
    Dodo->>GW: POST /payments/webhook
    GW->>PS: proxy (raw body + signature)
    PS->>PS: verify webhook signature
    alt payment succeeded
        PS->>PS: UPDATE payment to COMPLETED
        PS->>BS: PATCH booking to CONFIRMED
        PS->>K: publish booking.successful
        K->>NS: consume and send confirmation email
    else payment failed
        PS->>PS: UPDATE payment to FAILED
        PS->>BS: PATCH booking to FAILED
        PS->>K: publish booking.failed
        K->>NS: consume and send failure email
    end
```

### 3b. View My Bookings

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant BS as Booking Service

    U->>GW: GET /bookings [JWT]
    GW->>BS: proxy (user_id)
    BS-->>GW: List of BookingResponse
    GW-->>U: booking list
```

### 3c. View Booking Details + Payment

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant BS as Booking Service
    participant PS as Payment Service

    U->>GW: GET /bookings/{id} [JWT]
    GW->>BS: proxy
    BS-->>GW: BookingResponse
    U->>GW: GET /payments/booking/{id} [JWT]
    GW->>PS: proxy
    PS-->>GW: PaymentResponse
    GW-->>U: combined booking + payment details
```

---

## 4. Cancellation & Refund

### 4a. User Cancels a Booking

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant BS as Booking Service
    participant K as Kafka
    participant PS as Payment Service
    participant Auth as Auth Service
    participant NS as Notification Service

    U->>GW: DELETE /bookings/{id} [JWT]
    GW->>BS: proxy (user_id)
    BS->>BS: UPDATE booking to CANCELLED
    BS->>BS: release locked seats
    BS->>K: publish payment.refund_initiated
    BS->>K: publish notification.refund_initiated
    BS-->>GW: booking cancelled
    GW-->>U: confirmation

    Note over K,NS: Async Refund Processing
    K->>PS: consume payment.refund_initiated

    alt payment_method = DODO
        PS->>Dodo: create refund
        PS->>PS: UPDATE payment to REFUNDED
    else payment_method = WALLET
        PS->>Auth: POST /auth/wallet/internal/credit
        Auth->>Auth: credit wallet + log transaction
        PS->>PS: UPDATE payment to REFUNDED
    end

    PS->>K: publish notification.refund_completed
    K->>NS: consume and send refund confirmation email

    K->>NS: consume notification.refund_initiated
    NS->>NS: send "refund in progress" email
```

### 4b. Admin Cancels a Show (Cascade)

```mermaid
sequenceDiagram
    participant A as Admin
    participant GW as API Gateway
    participant ES as Event Service
    participant BS as Booking Service
    participant K as Kafka
    participant PS as Payment Service
    participant NS as Notification Service
    participant SS as Search Service

    A->>GW: DELETE /shows/{id} [JWT]
    GW->>ES: proxy
    ES->>ES: UPDATE show to CANCELLED
    ES->>BS: POST /bookings/cancel-by-show/{id}
    BS->>BS: cancel ALL bookings for show schedules
    BS->>K: publish payment.refund_initiated (per booking)
    BS->>K: publish notification.refund_initiated (per booking)
    ES->>K: publish search.show_changed (action=deleted)
    K->>SS: consume and delete show from Elasticsearch
    K->>PS: consume and process refunds
    K->>NS: consume and send cancellation emails
```

### 4c. Admin Marks Venue Inactive (Cascade)

```mermaid
sequenceDiagram
    participant A as Admin
    participant GW as API Gateway
    participant ES as Event Service
    participant BS as Booking Service
    participant K as Kafka
    participant SS as Search Service

    A->>GW: DELETE /venues/{id} [JWT]
    GW->>ES: proxy
    ES->>ES: UPDATE venue to INACTIVE
    ES->>BS: POST /bookings/cancel-by-venue/{id}
    BS->>BS: cancel ALL bookings under venue
    BS->>K: publish refund + notification events
    ES->>K: publish search.venue_changed (action=deleted)
    K->>SS: consume and remove venue from Elasticsearch
```

---

## 5. Admin Management

### 5a. Create Show + Upload Poster

```mermaid
sequenceDiagram
    participant A as Admin
    participant GW as API Gateway
    participant ES as Event Service
    participant S3 as MinIO
    participant K as Kafka
    participant SS as Search Service

    A->>GW: POST /shows/ [JWT]
    GW->>ES: proxy
    ES->>ES: INSERT show (ACTIVE)
    ES->>K: publish search.show_changed (action=created)
    K->>SS: consume and index in Elasticsearch
    ES-->>GW: ShowResponse

    A->>GW: POST /shows/{id}/poster [JWT + file]
    GW->>ES: proxy (multipart)
    ES->>S3: PUT poster image
    S3-->>ES: public URL
    ES->>ES: UPDATE show.poster_url = S3 URL
    ES-->>GW: ShowResponse (with poster_url)
```

### 5b. Create Venue

```mermaid
sequenceDiagram
    participant A as Admin
    participant GW as API Gateway
    participant ES as Event Service
    participant K as Kafka
    participant SS as Search Service

    A->>GW: POST /venues/ [JWT]
    GW->>ES: proxy
    ES->>ES: INSERT venue (ACTIVE)
    ES->>K: publish search.venue_changed (action=created)
    K->>SS: consume and index in Elasticsearch
    ES-->>GW: VenueResponse
```

### 5c. Create Screen + Schedule

```mermaid
sequenceDiagram
    participant A as Admin
    participant GW as API Gateway
    participant ES as Event Service

    Note over A,ES: Create Screen
    A->>GW: POST /screens/ { venue_id, name, capacity }
    GW->>ES: proxy
    ES->>ES: INSERT screen + auto-create seats
    ES-->>GW: ScreenResponse

    Note over A,ES: Create Schedule
    A->>GW: POST /schedules/ { show_id, screen_id, start_time }
    GW->>ES: proxy
    ES->>ES: validate venue hours + no overlap
    ES->>ES: INSERT schedule
    ES-->>GW: ScheduleResponse
```

### 5d. Edit Show / Venue

```mermaid
sequenceDiagram
    participant A as Admin
    participant GW as API Gateway
    participant ES as Event Service
    participant K as Kafka
    participant SS as Search Service

    A->>GW: PATCH /shows/{id} or /venues/{id} [JWT]
    GW->>ES: proxy
    ES->>ES: UPDATE record
    ES->>K: publish search.show_changed or venue_changed (action=updated)
    K->>SS: consume and re-index in Elasticsearch
    ES-->>GW: updated response
```

---

## 6. Infrastructure Startup (Docker Compose)

```mermaid
flowchart LR
    subgraph Infra Startup
        PG["PostgreSQL"] --> ESInit["es-init"]
        PG --> S3Init["s3-init"]
        ELS["Elasticsearch"] --> ESInit
        MINIO["MinIO"] --> S3Init

        ESInit --> |seeds shows/venues| ELS
        S3Init --> |uploads posters| MINIO
        S3Init --> |updates poster_url| PG
    end

    ESInit -.-> done1["Done, exits"]
    S3Init -.-> done2["Done, exits"]
```

---

## Kafka Event Map

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `booking.successful` | Payment Service | Notification Service | Send booking confirmation email |
| `booking.failed` | Payment Service | Notification Service | Send payment failure email |
| `payment.refund_initiated` | Booking Service | Payment Service | Process refund (Dodo or wallet) |
| `notification.refund_initiated` | Booking Service | Notification Service | Send "refund in progress" email |
| `notification.refund_completed` | Payment Service | Notification Service | Send "refund completed" email |
| `search.show_changed` | Event Service | Search Service | Index/update/delete show in ES |
| `search.venue_changed` | Event Service | Search Service | Index/update/delete venue in ES |

---

## Service Communication Map

| Source | Target | Method | When |
|--------|--------|--------|------|
| API Gateway | Auth Service | HTTP | every authenticated request (token verify) |
| API Gateway | Event Service | HTTP | show/venue/screen/schedule CRUD |
| API Gateway | Booking Service | HTTP | booking CRUD + seat availability |
| API Gateway | Payment Service | HTTP | payment creation + webhook |
| API Gateway | Search Service | HTTP | search queries |
| Event Service | Booking Service | HTTP | cascade cancel (show/venue deletion) |
| Payment Service | Booking Service | HTTP | update booking status after payment |
| Payment Service | Auth Service | HTTP | credit wallet for refund |
| Payment Service | Dodo Payments | HTTP | checkout session + refund API |
| Notification Service | Mailpit (SMTP) | SMTP | send email notifications |
| Frontend | MinIO (S3) | HTTP | load poster images directly |
