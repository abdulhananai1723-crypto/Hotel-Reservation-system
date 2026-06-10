import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime, date

DB_NAME = "hotel_system.db"

st.set_page_config(
    page_title="HotelPro Reservation System",
    page_icon="🏨",
    layout="wide"
)

# ---------------- PREMIUM STYLE ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #fff7ed 100%);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

.big-title {
    font-size: 44px;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.1;
}

.subtitle {
    font-size: 18px;
    color: #475569;
    margin-top: 10px;
    margin-bottom: 25px;
}

.hero {
    padding: 48px;
    border-radius: 30px;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 55%, #f97316 100%);
    color: white;
    box-shadow: 0 25px 60px rgba(37, 99, 235, 0.28);
    margin-bottom: 30px;
}

.hero h1 {
    font-size: 54px;
    font-weight: 900;
    margin-bottom: 10px;
    color: white;
}

.hero p {
    font-size: 19px;
    color: #e0e7ff;
}

.card {
    background: rgba(255,255,255,0.95);
    padding: 28px;
    border-radius: 24px;
    border: 1px solid rgba(226,232,240,0.9);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    margin-bottom: 20px;
}

.feature-card {
    background: white;
    padding: 24px;
    border-radius: 22px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
    text-align: center;
    min-height: 150px;
}

.feature-card h3 {
    color: #0f172a;
    font-weight: 800;
}

.feature-card p {
    color: #64748b;
}

div.stButton > button {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 0.75rem 1rem;
    font-weight: 700;
    box-shadow: 0 10px 25px rgba(37,99,235,0.25);
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #6d28d9);
    color: white;
    transform: translateY(-1px);
}

[data-testid="stMetric"] {
    background: white;
    padding: 20px;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 28px rgba(15,23,42,0.06);
}

.stAlert {
    border-radius: 16px;
}

input, textarea, select {
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------- DATABASE ----------------
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS owners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hotels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        hotel_name TEXT,
        location TEXT,
        phone TEXT,
        description TEXT,
        amenities TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        room_number TEXT,
        room_type TEXT,
        price INTEGER,
        capacity INTEGER,
        status TEXT,
        description TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        room_id INTEGER,
        customer_name TEXT,
        customer_email TEXT,
        customer_phone TEXT,
        guests INTEGER,
        check_in TEXT,
        check_out TEXT,
        nights INTEGER,
        total_price INTEGER,
        status TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def execute_query(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def fetch_all(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchall()
    conn.close()
    return data


def fetch_one(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchone()
    conn.close()
    return data


init_db()


# ---------------- AUTH ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def signup_owner(name, email, password):
    existing = fetch_one("SELECT id FROM owners WHERE email = ?", (email,))

    if existing:
        return False, "Email already registered."

    execute_query(
        "INSERT INTO owners (name, email, password, created_at) VALUES (?, ?, ?, ?)",
        (name, email, hash_password(password), now())
    )

    return True, "Account created successfully."


def login_owner(email, password):
    owner = fetch_one(
        "SELECT id, name, email FROM owners WHERE email = ? AND password = ?",
        (email, hash_password(password))
    )

    if owner:
        return True, {
            "id": owner[0],
            "name": owner[1],
            "email": owner[2]
        }

    return False, None


# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "owner" not in st.session_state:
    st.session_state.owner = None


def currency(amount):
    return f"PKR {int(amount):,}"


def logout():
    st.session_state.logged_in = False
    st.session_state.owner = None
    st.rerun()


# ---------------- AUTH PAGES ----------------
def login_page():
    st.markdown('<div class="big-title">🏨 Owner Login</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Login to manage your hotel, rooms, bookings and revenue.</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        success, owner = login_owner(email, password)

        if success:
            st.session_state.logged_in = True
            st.session_state.owner = owner
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid email or password.")

    st.markdown('</div>', unsafe_allow_html=True)


def signup_page():
    st.markdown('<div class="big-title">Create Owner Account</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Create your hotel owner account and start managing your property.</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)

    name = st.text_input("Owner Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Create Account", use_container_width=True):
        if not name or not email or not password:
            st.error("Please fill all fields.")
        elif password != confirm:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            success, message = signup_owner(name, email, password)
            if success:
                st.success(message)
            else:
                st.error(message)

    st.markdown('</div>', unsafe_allow_html=True)


# ---------------- PUBLIC BOOKING ----------------
def public_booking_page():
    st.markdown("""
    <div class="hero">
        <h1>Luxury Hotel Booking System</h1>
        <p>Book premium rooms instantly with a modern hotel reservation platform.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🏨 Premium Hotels</h3>
            <p>Find professional hotels with available rooms.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>⚡ Instant Booking</h3>
            <p>Confirm reservations quickly and securely.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Owner Dashboard</h3>
            <p>Manage hotels, rooms, bookings and revenue.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("## Available Hotels")

    hotels = fetch_all("""
        SELECT hotels.id, hotels.owner_id, hotels.hotel_name, hotels.location, hotels.phone, hotels.description
        FROM hotels
        JOIN rooms ON hotels.owner_id = rooms.owner_id
        WHERE rooms.status = 'Available'
        GROUP BY hotels.owner_id
    """)

    if not hotels:
        st.warning("No hotels with available rooms right now. Owner ko pehle hotel profile aur rooms add karne honge.")
        return

    hotel_options = {f"{h[2]} - {h[3]}": h for h in hotels}
    selected_hotel_name = st.selectbox("Select Hotel", list(hotel_options.keys()))
    hotel = hotel_options[selected_hotel_name]

    hotel_id, owner_id, hotel_name, location, phone, description = hotel

    st.markdown(f"""
    <div class="card">
        <h2>{hotel_name}</h2>
        <p><b>📍 Location:</b> {location}</p>
        <p><b>☎ Phone:</b> {phone}</p>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)

    rooms = fetch_all("""
        SELECT id, room_number, room_type, price, capacity, description
        FROM rooms
        WHERE owner_id = ? AND status = 'Available'
    """, (owner_id,))

    room_options = {
        f"Room {r[1]} | {r[2]} | {currency(r[3])}/night | Capacity {r[4]}": r
        for r in rooms
    }

    selected_room_label = st.selectbox("Select Room", list(room_options.keys()))
    room = room_options[selected_room_label]

    room_id, room_number, room_type, price, capacity, room_description = room

    st.markdown(f"""
    <div class="card">
        <h3>Selected Room</h3>
        <p><b>Room Number:</b> {room_number}</p>
        <p><b>Room Type:</b> {room_type}</p>
        <p><b>Price:</b> {currency(price)} per night</p>
        <p><b>Capacity:</b> {capacity} guests</p>
        <p>{room_description}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Customer Details")

    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name")
        customer_email = st.text_input("Customer Email")
        customer_phone = st.text_input("Customer Phone")

    with col2:
        guests = st.number_input("Guests", min_value=1, max_value=int(capacity))
        check_in = st.date_input("Check-in", min_value=date.today())
        check_out = st.date_input("Check-out", min_value=date.today())

    if check_out > check_in:
        nights = (check_out - check_in).days
        total_price = nights * int(price)

        col_a, col_b = st.columns(2)
        col_a.success(f"Nights: {nights}")
        col_b.info(f"Total Price: {currency(total_price)}")
    else:
        nights = 0
        total_price = 0
        st.warning("Check-out date must be after check-in date.")

    if st.button("Confirm Booking", use_container_width=True):
        if customer_name and customer_email and customer_phone and nights > 0:
            execute_query("""
                INSERT INTO bookings (
                    owner_id, room_id, customer_name, customer_email, customer_phone,
                    guests, check_in, check_out, nights, total_price, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                owner_id, room_id, customer_name, customer_email, customer_phone,
                guests, str(check_in), str(check_out), nights, total_price,
                "Confirmed", now()
            ))

            execute_query(
                "UPDATE rooms SET status = 'Booked' WHERE id = ?",
                (room_id,)
            )

            st.success("Booking confirmed successfully.")
            st.balloons()
        else:
            st.error("Please complete all fields correctly.")


# ---------------- OWNER DASHBOARD ----------------
def dashboard_home(owner_id):
    st.markdown('<div class="big-title">Owner Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Track your hotel performance, bookings and revenue.</div>', unsafe_allow_html=True)

    total_rooms = fetch_one("SELECT COUNT(*) FROM rooms WHERE owner_id = ?", (owner_id,))[0]
    available_rooms = fetch_one("SELECT COUNT(*) FROM rooms WHERE owner_id = ? AND status = 'Available'", (owner_id,))[0]
    booked_rooms = fetch_one("SELECT COUNT(*) FROM rooms WHERE owner_id = ? AND status = 'Booked'", (owner_id,))[0]
    total_bookings = fetch_one("SELECT COUNT(*) FROM bookings WHERE owner_id = ?", (owner_id,))[0]
    revenue = fetch_one("SELECT COALESCE(SUM(total_price), 0) FROM bookings WHERE owner_id = ?", (owner_id,))[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Rooms", total_rooms)
    col2.metric("Available Rooms", available_rooms)
    col3.metric("Booked Rooms", booked_rooms)
    col4.metric("Revenue", currency(revenue))

    st.divider()

    bookings = fetch_all("""
        SELECT created_at, total_price, status
        FROM bookings
        WHERE owner_id = ?
        ORDER BY created_at DESC
    """, (owner_id,))

    if bookings:
        df = pd.DataFrame(bookings, columns=["Created At", "Revenue", "Status"])
        df["Created At"] = pd.to_datetime(df["Created At"]).dt.date

        chart_df = df.groupby("Created At")["Revenue"].sum().reset_index()
        fig = px.line(chart_df, x="Created At", y="Revenue", title="Revenue Trend")
        st.plotly_chart(fig, use_container_width=True)

        status_df = df["Status"].value_counts().reset_index()
        status_df.columns = ["Status", "Count"]
        fig2 = px.pie(status_df, names="Status", values="Count", title="Booking Status")
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Recent Bookings")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No booking data yet.")


def hotel_profile(owner_id):
    st.markdown('<div class="big-title">Hotel Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Add your hotel details so customers can book rooms.</div>', unsafe_allow_html=True)

    hotel = fetch_one("""
        SELECT hotel_name, location, phone, description, amenities
        FROM hotels
        WHERE owner_id = ?
    """, (owner_id,))

    hotel_name = st.text_input("Hotel Name", value=hotel[0] if hotel else "")
    location = st.text_input("Location", value=hotel[1] if hotel else "")
    phone = st.text_input("Phone", value=hotel[2] if hotel else "")
    description = st.text_area("Hotel Description", value=hotel[3] if hotel else "")
    amenities = st.text_area("Amenities", value=hotel[4] if hotel else "WiFi, Parking, AC, Restaurant")

    if st.button("Save Hotel Profile", use_container_width=True):
        if not hotel_name or not location:
            st.error("Hotel name and location are required.")
            return

        existing = fetch_one("SELECT id FROM hotels WHERE owner_id = ?", (owner_id,))

        if existing:
            execute_query("""
                UPDATE hotels
                SET hotel_name = ?, location = ?, phone = ?, description = ?, amenities = ?
                WHERE owner_id = ?
            """, (hotel_name, location, phone, description, amenities, owner_id))
        else:
            execute_query("""
                INSERT INTO hotels (owner_id, hotel_name, location, phone, description, amenities)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (owner_id, hotel_name, location, phone, description, amenities))

        st.success("Hotel profile saved successfully.")


def manage_rooms(owner_id):
    st.markdown('<div class="big-title">Manage Rooms</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Add rooms, update availability, and manage pricing.</div>', unsafe_allow_html=True)

    with st.expander("Add New Room", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            room_number = st.text_input("Room Number")
            room_type = st.selectbox("Room Type", ["Single", "Double", "Deluxe", "Suite", "Family"])
            price = st.number_input("Price per Night", min_value=1000, step=500)

        with col2:
            capacity = st.number_input("Capacity", min_value=1, max_value=10)
            status = st.selectbox("Room Status", ["Available", "Booked", "Maintenance"])
            description = st.text_area("Room Description")

        if st.button("Add Room", use_container_width=True):
            if room_number:
                execute_query("""
                    INSERT INTO rooms (
                        owner_id, room_number, room_type, price, capacity, status, description
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (owner_id, room_number, room_type, price, capacity, status, description))

                st.success("Room added successfully.")
                st.rerun()
            else:
                st.error("Room number is required.")

    rooms = fetch_all("""
        SELECT id, room_number, room_type, price, capacity, status, description
        FROM rooms
        WHERE owner_id = ?
        ORDER BY id DESC
    """, (owner_id,))

    if rooms:
        df = pd.DataFrame(
            rooms,
            columns=["ID", "Room Number", "Type", "Price", "Capacity", "Status", "Description"]
        )

        st.subheader("Your Rooms")
        st.dataframe(df, use_container_width=True)

        st.subheader("Update Room Status")
        room_ids = df["ID"].tolist()
        selected_id = st.selectbox("Select Room ID", room_ids)
        new_status = st.selectbox("New Status", ["Available", "Booked", "Maintenance"])

        if st.button("Update Status", use_container_width=True):
            execute_query("UPDATE rooms SET status = ? WHERE id = ?", (new_status, selected_id))
            st.success("Room status updated.")
            st.rerun()
    else:
        st.info("No rooms added yet.")


def reservations(owner_id):
    st.markdown('<div class="big-title">Reservations</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">View and manage customer bookings.</div>', unsafe_allow_html=True)

    data = fetch_all("""
        SELECT 
            bookings.id,
            rooms.room_number,
            rooms.room_type,
            bookings.customer_name,
            bookings.customer_email,
            bookings.customer_phone,
            bookings.guests,
            bookings.check_in,
            bookings.check_out,
            bookings.nights,
            bookings.total_price,
            bookings.status
        FROM bookings
        JOIN rooms ON bookings.room_id = rooms.id
        WHERE bookings.owner_id = ?
        ORDER BY bookings.id DESC
    """, (owner_id,))

    if not data:
        st.info("No reservations yet.")
        return

    df = pd.DataFrame(data, columns=[
        "Booking ID", "Room", "Type", "Customer", "Email", "Phone",
        "Guests", "Check-in", "Check-out", "Nights", "Total", "Status"
    ])

    st.dataframe(df, use_container_width=True)

    st.subheader("Update Booking Status")
    booking_id = st.selectbox("Select Booking ID", df["Booking ID"].tolist())
    status = st.selectbox("Status", ["Confirmed", "Checked In", "Checked Out", "Cancelled"])

    if st.button("Update Booking", use_container_width=True):
        execute_query("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))

        if status in ["Checked Out", "Cancelled"]:
            room_id = fetch_one("SELECT room_id FROM bookings WHERE id = ?", (booking_id,))[0]
            execute_query("UPDATE rooms SET status = 'Available' WHERE id = ?", (room_id,))

        st.success("Booking updated successfully.")
        st.rerun()

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Reservations CSV",
        csv,
        "reservations.csv",
        "text/csv",
        use_container_width=True
    )


def owner_app():
    owner = st.session_state.owner
    owner_id = owner["id"]

    st.sidebar.title("🏨 HotelPro")
    st.sidebar.success(f"Owner: {owner['name']}")

    page = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Hotel Profile", "Manage Rooms", "Reservations", "Logout"]
    )

    if page == "Dashboard":
        dashboard_home(owner_id)
    elif page == "Hotel Profile":
        hotel_profile(owner_id)
    elif page == "Manage Rooms":
        manage_rooms(owner_id)
    elif page == "Reservations":
        reservations(owner_id)
    elif page == "Logout":
        logout()


# ---------------- MAIN ----------------
if st.session_state.logged_in:
    owner_app()
else:
    st.sidebar.title("🏨 HotelPro")

    page = st.sidebar.radio(
        "Navigation",
        ["Book Room", "Owner Login", "Owner Signup"]
    )

    if page == "Book Room":
        public_booking_page()
    elif page == "Owner Login":
        login_page()
    elif page == "Owner Signup":
        signup_page()
