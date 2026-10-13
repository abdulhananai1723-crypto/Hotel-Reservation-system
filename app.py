
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import hmac
import secrets
import re
import html
from datetime import datetime, date, timedelta
from pathlib import Path

st.set_page_config(
    page_title="HotelPro Elite | Luxury Management",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = Path(__file__).resolve().parent / "hotelpro_elite.db"

# =========================
# LUXURY THEME
# =========================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap');

:root {
    --gold: #D7B878;
    --goldlight: #F4DFAD;
    --black: #0B0D0E;
    --card: #171A1C;
    --border: #45402F;
    --muted: #B5B0A4;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background:
        radial-gradient(
            ellipse at 80% 0%,
            rgba(190,151,79,.10),
            transparent 40%
        ),
        #0B0D0E;
    color: #F5F0E5;
}

[data-testid="stSidebar"] {
    background: #111416;
    border-right: 1px solid #3D382D;
}

h1, h2, h3 {
    color: #F5E8CA !important;
}

.hero {
    padding: 48px 38px;
    border-radius: 24px;
    background:
        linear-gradient(
            120deg,
            #181B1D 0%,
            #29251C 65%,
            #17191A 100%
        );
    border: 1px solid #6C5734;
    box-shadow: 0 20px 50px rgba(0,0,0,.25);
    margin-bottom: 28px;
}

.hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.1rem,4vw,3.5rem);
    color: #F5DEAA !important;
    margin: 8px 0;
}

.hero p {
    color: #C8C0B0;
    font-size: 1.05rem;
}

.eyebrow {
    color: #D7B878;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 3px;
}

.lux-card {
    padding: 25px;
    border-radius: 18px;
    background: linear-gradient(145deg,#1D2021,#151718);
    border: 1px solid #48402E;
    margin-bottom: 18px;
    min-height: 135px;
}

.lux-card h3 {
    color: #F1D79D !important;
    margin: 8px 0;
}

.lux-card p {
    color: #BDB6A7;
    margin: 0;
}

.gold-title {
    color: #D7B878;
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: 800;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg,#202223,#17191A);
    border: 1px solid #514631;
    border-radius: 17px;
    padding: 20px;
}

[data-testid="stMetricValue"] {
    color: #F2D99F;
}

div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(110deg,#C9A35E,#F2D99F);
    color: #171717 !important;
    border: 1px solid #E8CD91;
    border-radius: 11px;
    font-weight: 800;
    min-height: 46px;
}

div.stButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
    background: #F5E0AE;
    color: #111 !important;
}

div.stButton > button:not([kind="primary"]) {
    background: #222526;
    color: #F2D99F;
    border: 1px solid #625336;
    border-radius: 11px;
}

div[data-testid="stForm"] {
    background: #181B1C;
    border: 1px solid #4C422F;
    border-radius: 18px;
    padding: 24px;
}

[data-testid="stDataFrame"] {
    border: 1px solid #4C422F;
    border-radius: 12px;
    overflow: hidden;
}

[data-baseweb="tab"][aria-selected="true"] {
    color: #E6C889 !important;
}

.stAlert {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


def safe(value):
    return html.escape(str(value or ""), quote=True)


def hero(title, subtitle, eyebrow="HOTELPRO ELITE"):
    st.markdown(f"""
    <div class="hero">
        <div class="eyebrow">{safe(eyebrow)}</div>
        <h1>{safe(title)}</h1>
        <p>{safe(subtitle)}</p>
    </div>
    """, unsafe_allow_html=True)


def feature(title, description):
    st.markdown(f"""
    <div class="lux-card">
        <div class="gold-title">✦ ELITE FEATURE</div>
        <h3>{safe(title)}</h3>
        <p>{safe(description)}</p>
    </div>
    """, unsafe_allow_html=True)


def money(amount):
    return f"PKR {float(amount):,.0f}"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========================
# DATABASE
# =========================

def connect():
    c = sqlite3.connect(DB, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA busy_timeout=15000")
    return c


def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL UNIQUE,
            hotel_name TEXT NOT NULL,
            location TEXT NOT NULL,
            phone TEXT,
            description TEXT,
            amenities TEXT,
            FOREIGN KEY(owner_id) REFERENCES owners(id)
        );

        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            room_number TEXT NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL CHECK(price>=0),
            capacity INTEGER NOT NULL CHECK(capacity>0),
            status TEXT NOT NULL DEFAULT 'Available',
            description TEXT,
            UNIQUE(owner_id,room_number),
            FOREIGN KEY(owner_id) REFERENCES owners(id)
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            guests INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            nights INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(owner_id) REFERENCES owners(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        );

        CREATE INDEX IF NOT EXISTS idx_booking_dates
        ON bookings(room_id,check_in,check_out,status);
        """)


init_db()


def fetch_all(sql, args=()):
    with connect() as c:
        return [
            dict(row)
            for row in c.execute(sql, args).fetchall()
        ]


def fetch_one(sql, args=()):
    with connect() as c:
        row = c.execute(sql, args).fetchone()
        return dict(row) if row else None


def execute(sql, args=()):
    with connect() as c:
        cur = c.execute(sql, args)
        return cur.lastrowid


# =========================
# SECURE PASSWORDS
# =========================

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        600000
    )
    return (
        "pbkdf2_sha256$600000$"
        + salt.hex()
        + "$"
        + digest.hex()
    )


def verify_password(password, stored):
    try:
        algorithm, rounds, salt, digest = stored.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt),
            int(rounds)
        )

        return hmac.compare_digest(
            calculated,
            bytes.fromhex(digest)
        )
    except (ValueError, TypeError):
        return False


def signup(name, email, password):
    try:
        execute("""
            INSERT INTO owners(name,email,password,created_at)
            VALUES(?,?,?,?)
        """, (
            name.strip(),
            email.strip().lower(),
            hash_password(password),
            now()
        ))
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "Email already registered."


def login(email, password):
    owner = fetch_one(
        "SELECT * FROM owners WHERE email=?",
        (email.strip().lower(),)
    )

    if owner and verify_password(
        password,
        owner["password"]
    ):
        return {
            "id": owner["id"],
            "name": owner["name"],
            "email": owner["email"]
        }

    return None


# =========================
# SESSION
# =========================

if "owner" not in st.session_state:
    st.session_state.owner = None

if "booking_receipt" not in st.session_state:
    st.session_state.booking_receipt = None


def logout():
    st.session_state.owner = None
    st.rerun()


# =========================
# DATE-WISE AVAILABILITY
# =========================

ACTIVE_STATUSES = (
    "Confirmed",
    "Checked In",
    "Checked Out"
)


def available_rooms(owner_id, check_in, check_out):
    return fetch_all("""
        SELECT r.*
        FROM rooms r
        WHERE r.owner_id=?
        AND r.status='Available'
        AND NOT EXISTS (
            SELECT 1 FROM bookings b
            WHERE b.room_id=r.id
            AND b.status IN (
                'Confirmed','Checked In','Checked Out'
            )
            AND b.check_in < ?
            AND b.check_out > ?
        )
        ORDER BY r.room_number
    """, (
        owner_id,
        str(check_out),
        str(check_in)
    ))


def create_booking(
    owner_id,
    room_id,
    name,
    email,
    phone,
    guests,
    check_in,
    check_out
):
    nights = (check_out - check_in).days

    if nights <= 0:
        return False, "Invalid booking dates."

    try:
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")

            room = c.execute("""
                SELECT * FROM rooms
                WHERE id=? AND owner_id=? AND status='Available'
            """, (room_id, owner_id)).fetchone()

            if not room:
                return False, "Room is unavailable."

            if guests > room["capacity"]:
                return False, "Guest capacity exceeded."

            conflict = c.execute("""
                SELECT id FROM bookings
                WHERE room_id=?
                AND status IN (
                    'Confirmed','Checked In','Checked Out'
                )
                AND check_in < ?
                AND check_out > ?
                LIMIT 1
            """, (
                room_id,
                str(check_out),
                str(check_in)
            )).fetchone()

            if conflict:
                return False, "Room is booked for these dates."

            total = nights * room["price"]

            cur = c.execute("""
                INSERT INTO bookings(
                    owner_id,room_id,customer_name,
                    customer_email,customer_phone,
                    guests,check_in,check_out,nights,
                    total_price,status,created_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                owner_id,
                room_id,
                name,
                email,
                phone,
                guests,
                str(check_in),
                str(check_out),
                nights,
                total,
                "Confirmed",
                now()
            ))

            booking_id = cur.lastrowid

        return True, booking_id

    except sqlite3.Error:
        return False, "Database error. Please try again."


# =========================
# PUBLIC BOOKING PAGE
# =========================

def booking_page():
    hero(
        "Experience Exceptional Hospitality",
        "Discover refined stays, elegant rooms and effortless reservations.",
        "✦ THE ART OF LUXURY STAYS"
    )

    a, b, c = st.columns(3)

    with a:
        feature(
            "Curated Hotels",
            "Explore beautiful properties and premium accommodation."
        )

    with b:
        feature(
            "Seamless Booking",
            "Reserve your ideal room in just a few simple steps."
        )

    with c:
        feature(
            "Trusted Management",
            "A complete digital experience for guests and hotel owners."
        )

    st.subheader("Explore Our Hotels")

    hotels = fetch_all("""
        SELECT * FROM hotels
        ORDER BY hotel_name
    """)

    if not hotels:
        st.info(
            "No hotels are listed yet. "
            "An owner can add a hotel after signing in."
        )
        return

    hotel_map = {
        f"{h['hotel_name']} — {h['location']} (#{h['id']})": h
        for h in hotels
    }

    chosen = st.selectbox(
        "Choose your hotel",
        list(hotel_map)
    )

    hotel = hotel_map[chosen]

    st.markdown(f"""
    <div class="lux-card">
        <div class="gold-title">FEATURED PROPERTY</div>
        <h3>{safe(hotel['hotel_name'])}</h3>
        <p>📍 {safe(hotel['location'])}</p>
        <p>☎ {safe(hotel['phone'])}</p>
        <p>{safe(hotel['description'])}</p>
        <p>✦ {safe(hotel['amenities'])}</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Select Your Stay")

    col1, col2 = st.columns(2)

    with col1:
        check_in = st.date_input(
            "Check-in date",
            min_value=date.today(),
            value=date.today(),
            key="public_checkin"
        )

    with col2:
        check_out = st.date_input(
            "Check-out date",
            min_value=check_in + timedelta(days=1),
            value=check_in + timedelta(days=1),
            key="public_checkout"
        )

    if check_out <= check_in:
        st.warning("Check-out must be after check-in.")
        return

    rooms = available_rooms(
        hotel["owner_id"],
        check_in,
        check_out
    )

    if not rooms:
        st.warning(
            "No rooms available for your selected dates."
        )
        return

    room_map = {
        f"Room {r['room_number']} · {r['room_type']} "
        f"· {money(r['price'])}/night": r
        for r in rooms
    }

    selected = st.selectbox(
        "Available rooms",
        list(room_map)
    )

    room = room_map[selected]
    nights = (check_out - check_in).days
    total = nights * room["price"]

    a, b, c = st.columns(3)
    a.metric("Nightly Rate", money(room["price"]))
    b.metric("Nights", nights)
    c.metric("Total Stay", money(total))

    st.caption(
        f"Capacity: {room['capacity']} guests · "
        f"{room['description'] or 'Premium accommodation'}"
    )

    st.subheader("Guest Information")

    with st.form("booking_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")

        guests = st.number_input(
            "Number of Guests",
            min_value=1,
            max_value=int(room["capacity"]),
            value=1
        )

        agree = st.checkbox(
            "I confirm that my booking information is correct."
        )

        submit = st.form_submit_button(
            "Confirm Reservation",
            type="primary",
            use_container_width=True
        )

    if submit:
        if not all([
            name.strip(),
            email.strip(),
            phone.strip(),
            agree
        ]):
            st.error("Complete all required fields.")

        elif not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email.strip()
        ):
            st.error("Enter a valid email address.")

        else:
            success, result = create_booking(
                hotel["owner_id"],
                room["id"],
                name.strip(),
                email.strip(),
                phone.strip(),
                int(guests),
                check_in,
                check_out
            )

            if success:
                st.session_state.booking_receipt = {
                    "id": result,
                    "hotel": hotel["hotel_name"],
                    "guest": name.strip(),
                    "total": total
                }
                st.rerun()
            else:
                st.error(result)

    receipt = st.session_state.booking_receipt

    if receipt:
        st.success(
            f"Reservation #{receipt['id']} confirmed!"
        )
        st.info(
            f"{receipt['guest']} · {receipt['hotel']} · "
            f"{money(receipt['total'])}"
        )
        st.caption(
            "Reservation recorded. Payment is not processed "
            "through this application."
        )


# =========================
# OWNER AUTHENTICATION
# =========================

def auth_page():
    hero(
        "Hotel Owner Portal",
        "Manage your hospitality business with confidence.",
        "✦ PRIVATE MANAGEMENT ACCESS"
    )

    tab1, tab2 = st.tabs([
        "Owner Login",
        "Create Account"
    ])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            submitted = st.form_submit_button(
                "Sign In",
                type="primary",
                use_container_width=True
            )

        if submitted:
            owner = login(email, password)

            if owner:
                st.session_state.owner = owner
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with tab2:
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Business Email")
            password = st.text_input(
                "Create Password",
                type="password"
            )
            confirm = st.text_input(
                "Confirm Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Create Owner Account",
                type="primary",
                use_container_width=True
            )

        if submitted:
            if not name.strip():
                st.error("Enter your name.")

            elif not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                email.strip()
            ):
                st.error("Enter a valid email.")

            elif len(password) < 10:
                st.error(
                    "Password must contain at least 10 characters."
                )

            elif password != confirm:
                st.error("Passwords do not match.")

            else:
                success, message = signup(
                    name,
                    email,
                    password
                )

                if success:
                    st.success(message + " You can now log in.")
                else:
                    st.error(message)


# =========================
# OWNER DASHBOARD
# =========================

def dashboard(owner_id):
    hero(
        "Executive Dashboard",
        "A refined overview of your hotel's performance.",
        "✦ BUSINESS INTELLIGENCE"
    )

    rooms = fetch_one("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status='Available'
                THEN 1 ELSE 0 END) AS available,
            SUM(CASE WHEN status='Maintenance'
                THEN 1 ELSE 0 END) AS maintenance
        FROM rooms WHERE owner_id=?
    """, (owner_id,))

    bookings = fetch_one("""
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(
                CASE WHEN status!='Cancelled'
                THEN total_price ELSE 0 END
            ),0) AS revenue
        FROM bookings WHERE owner_id=?
    """, (owner_id,))

    cols = st.columns(4)

    cols[0].metric("Total Rooms", rooms["total"])
    cols[1].metric(
        "Active Rooms",
        rooms["available"] or 0
    )
    cols[2].metric("Reservations", bookings["total"])
    cols[3].metric(
        "Booked Revenue",
        money(bookings["revenue"])
    )

    st.caption(
        "Booked revenue is the value of non-cancelled "
        "reservations, not verified payments."
    )

    data = fetch_all("""
        SELECT
            created_at,
            total_price,
            status,
            customer_name
        FROM bookings
        WHERE owner_id=?
        ORDER BY created_at DESC
    """, (owner_id,))

    if not data:
        st.info(
            "No bookings yet. Add your hotel profile and rooms "
            "to start receiving reservations."
        )
        return

    df = pd.DataFrame(data)
    df["created_at"] = pd.to_datetime(df["created_at"])

    active = df[df["status"] != "Cancelled"].copy()

    if not active.empty:
        chart = (
            active.groupby(
                active["created_at"].dt.date
            )["total_price"]
            .sum()
            .reset_index()
        )

        chart.columns = ["Date", "Booked Revenue"]

        st.subheader("Revenue Performance")
        st.line_chart(
            chart.set_index("Date"),
            color="#D7B878"
        )

    st.subheader("Reservation Status")

    status_df = (
        df["status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Count")
    )

    st.bar_chart(
        status_df.set_index("Status"),
        color="#D7B878"
    )

    st.subheader("Recent Reservations")
    st.dataframe(
        df.head(10),
        hide_index=True,
        use_container_width=True
    )


# =========================
# HOTEL PROFILE
# =========================

def hotel_profile(owner_id):
    hero(
        "Hotel Profile",
        "Build a beautiful digital identity for your property.",
        "✦ PROPERTY SETTINGS"
    )

    hotel = fetch_one(
        "SELECT * FROM hotels WHERE owner_id=?",
        (owner_id,)
    )

    with st.form("hotel_form"):
        name = st.text_input(
            "Hotel Name",
            value=hotel["hotel_name"] if hotel else ""
        )

        location = st.text_input(
            "Location",
            value=hotel["location"] if hotel else ""
        )

        phone = st.text_input(
            "Contact Number",
            value=hotel["phone"] or "" if hotel else ""
        )

        description = st.text_area(
            "Property Description",
            value=hotel["description"] or "" if hotel else ""
        )

        amenities = st.text_area(
            "Amenities",
            value=hotel["amenities"] or "" if hotel
            else "Wi-Fi, Air Conditioning, Parking"
        )

        save = st.form_submit_button(
            "Save Hotel Profile",
            type="primary"
        )

    if save:
        if not name.strip() or not location.strip():
            st.error("Hotel name and location are required.")
            return

        if hotel:
            execute("""
                UPDATE hotels
                SET hotel_name=?,location=?,phone=?,
                    description=?,amenities=?
                WHERE owner_id=?
            """, (
                name.strip(),
                location.strip(),
                phone.strip(),
                description.strip(),
                amenities.strip(),
                owner_id
            ))
        else:
            execute("""
                INSERT INTO hotels(
                    owner_id,hotel_name,location,phone,
                    description,amenities
                )
                VALUES(?,?,?,?,?,?)
            """, (
                owner_id,
                name.strip(),
                location.strip(),
                phone.strip(),
                description.strip(),
                amenities.strip()
            ))

        st.success("Hotel profile saved successfully.")
        st.rerun()


# =========================
# ROOM MANAGEMENT
# =========================

def manage_rooms(owner_id):
    hero(
        "Room Collection",
        "Curate your accommodation inventory and pricing.",
        "✦ INVENTORY MANAGEMENT"
    )

    with st.expander("➕ Add New Room", expanded=True):
        with st.form("add_room"):
            a, b = st.columns(2)

            with a:
                number = st.text_input("Room Number")
                room_type = st.selectbox(
                    "Room Category",
                    [
                        "Standard",
                        "Deluxe",
                        "Executive",
                        "Suite",
                        "Family",
                        "Presidential Suite"
                    ]
                )
                price = st.number_input(
                    "Price Per Night (PKR)",
                    min_value=0.0,
                    value=5000.0,
                    step=500.0
                )

            with b:
                capacity = st.number_input(
                    "Guest Capacity",
                    min_value=1,
                    max_value=30,
                    value=2
                )
                status = st.selectbox(
                    "Room Availability Status",
                    ["Available", "Maintenance"]
                )
                description = st.text_area(
                    "Room Description"
                )

            save = st.form_submit_button(
                "Add Room",
                type="primary"
            )

        if save:
            if not number.strip():
                st.error("Enter a room number.")
            else:
                try:
                    execute("""
                        INSERT INTO rooms(
                            owner_id,room_number,room_type,
                            price,capacity,status,description
                        )
                        VALUES(?,?,?,?,?,?,?)
                    """, (
                        owner_id,
                        number.strip(),
                        room_type,
                        price,
                        int(capacity),
                        status,
                        description.strip()
                    ))
                    st.success("Room added successfully.")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error("This room number already exists.")

    rooms = fetch_all("""
        SELECT * FROM rooms
        WHERE owner_id=?
        ORDER BY room_number
    """, (owner_id,))

    if not rooms:
        st.info("No rooms added yet.")
        return

    st.subheader("Your Room Inventory")

    st.dataframe(
        pd.DataFrame(rooms),
        hide_index=True,
        use_container_width=True
    )

    room_map = {
        f"Room {r['room_number']} — {r['room_type']}": r
        for r in rooms
    }

    selected = st.selectbox(
        "Select room to edit",
        list(room_map)
    )

    room = room_map[selected]

    with st.form(f"edit_room_{room['id']}"):
        number = st.text_input(
            "Room Number",
            value=room["room_number"]
        )

        categories = [
            "Standard",
            "Deluxe",
            "Executive",
            "Suite",
            "Family",
            "Presidential Suite"
        ]

        room_type = st.selectbox(
            "Category",
            categories,
            index=categories.index(room["room_type"])
            if room["room_type"] in categories else 0
        )

        price = st.number_input(
            "Nightly Price",
            min_value=0.0,
            value=float(room["price"])
        )

        capacity = st.number_input(
            "Capacity",
            min_value=1,
            value=int(room["capacity"])
        )

        status = st.selectbox(
            "Operational Status",
            ["Available", "Maintenance"],
            index=0 if room["status"] == "Available" else 1
        )

        description = st.text_area(
            "Description",
            value=room["description"] or ""
        )

        update = st.form_submit_button(
            "Update Room",
            type="primary"
        )

    if update:
        try:
            execute("""
                UPDATE rooms
                SET room_number=?,room_type=?,price=?,
                    capacity=?,status=?,description=?
                WHERE id=? AND owner_id=?
            """, (
                number.strip(),
                room_type,
                price,
                int(capacity),
                status,
                description.strip(),
                room["id"],
                owner_id
            ))

            st.success("Room updated.")
            st.rerun()

        except sqlite3.IntegrityError:
            st.error("Room number already exists.")


# =========================
# RESERVATIONS
# =========================

def reservations(owner_id):
    hero(
        "Reservation Concierge",
        "Every guest journey, beautifully organized.",
        "✦ BOOKING OPERATIONS"
    )

    rows = fetch_all("""
        SELECT
            b.*,
            r.room_number,
            r.room_type
        FROM bookings b
        JOIN rooms r ON r.id=b.room_id
        WHERE b.owner_id=?
        ORDER BY b.id DESC
    """, (owner_id,))

    if not rows:
        st.info("No reservations available.")
        return

    df = pd.DataFrame(rows)

    a, b, c = st.columns(3)
    a.metric("Total Reservations", len(df))
    b.metric(
        "Confirmed",
        int((df["status"] == "Confirmed").sum())
    )
    c.metric(
        "Cancelled",
        int((df["status"] == "Cancelled").sum())
    )

    status_filter = st.selectbox(
        "Filter reservations",
        [
            "All",
            "Confirmed",
            "Checked In",
            "Checked Out",
            "Cancelled"
        ]
    )

    display = df.copy()

    if status_filter != "All":
        display = display[
            display["status"] == status_filter
        ]

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True
    )

    booking_map = {
        f"#{r['id']} · {r['customer_name']} "
        f"· Room {r['room_number']}": r
        for r in rows
    }

    selected = st.selectbox(
        "Select Reservation",
        list(booking_map)
    )

    booking = booking_map[selected]

    st.write(
        f"**Current status:** {booking['status']}"
    )

    allowed = {
        "Confirmed": [
            "Confirmed",
            "Checked In",
            "Cancelled"
        ],
        "Checked In": [
            "Checked In",
            "Checked Out"
        ],
        "Checked Out": ["Checked Out"],
        "Cancelled": ["Cancelled"]
    }

    status = st.selectbox(
        "Update Status",
        allowed.get(
            booking["status"],
            [booking["status"]]
        )
    )

    if st.button(
        "Save Reservation Status",
        type="primary"
    ):
        if status == "Checked In":
            if not (
                date.fromisoformat(booking["check_in"])
                <= date.today()
                < date.fromisoformat(booking["check_out"])
            ):
                st.error(
                    "Check-in is only allowed during "
                    "the booked stay dates."
                )
                return

        execute("""
            UPDATE bookings
            SET status=?
            WHERE id=? AND owner_id=?
        """, (
            status,
            booking["id"],
            owner_id
        ))

        st.success("Reservation updated.")
        st.rerun()

    st.divider()

    st.download_button(
        "⬇ Export Reservations CSV",
        df.to_csv(index=False).encode("utf-8-sig"),
        file_name="hotelpro_reservations.csv",
        mime="text/csv",
        use_container_width=True
    )


# =========================
# MAIN NAVIGATION
# =========================

with st.sidebar:
    st.markdown("## ✦ HOTELPRO ELITE")
    st.caption("LUXURY HOSPITALITY SUITE")
    st.divider()

    owner = st.session_state.owner

    if owner:
        st.success(f"Welcome, {owner['name']}")

        page = st.radio(
            "Management",
            [
                "Dashboard",
                "Hotel Profile",
                "Manage Rooms",
                "Reservations",
                "Public Booking Preview"
            ]
        )

        st.divider()

        if st.button(
            "Sign Out",
            use_container_width=True
        ):
            logout()

    else:
        page = st.radio(
            "Explore",
            [
                "Book a Room",
                "Owner Portal"
            ]
        )

    st.divider()
    st.caption("HotelPro Elite • Luxury Edition")


if st.session_state.owner:
    owner_id = st.session_state.owner["id"]

    if page == "Dashboard":
        dashboard(owner_id)

    elif page == "Hotel Profile":
        hotel_profile(owner_id)

    elif page == "Manage Rooms":
        manage_rooms(owner_id)

    elif page == "Reservations":
        reservations(owner_id)

    elif page == "Public Booking Preview":
        booking_page()

else:
    if page == "Book a Room":
        booking_page()

    elif page == "Owner Portal":
        auth_page()
