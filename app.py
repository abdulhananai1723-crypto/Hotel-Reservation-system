import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import date

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Hotel Reservation System",
    page_icon="🏨",
    layout="wide"
)

DATA_DIR = "data"
OWNERS_FILE = f"{DATA_DIR}/owners.csv"
HOTELS_FILE = f"{DATA_DIR}/hotels.csv"
ROOMS_FILE = f"{DATA_DIR}/rooms.csv"
RESERVATIONS_FILE = f"{DATA_DIR}/reservations.csv"

os.makedirs(DATA_DIR, exist_ok=True)


# ---------------- HELPERS ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_files():
    if not os.path.exists(OWNERS_FILE):
        pd.DataFrame(columns=["username", "password"]).to_csv(OWNERS_FILE, index=False)

    if not os.path.exists(HOTELS_FILE):
        pd.DataFrame(columns=["owner", "hotel_name", "location", "phone"]).to_csv(HOTELS_FILE, index=False)

    if not os.path.exists(ROOMS_FILE):
        pd.DataFrame(columns=["owner", "room_name", "room_type", "price", "available"]).to_csv(ROOMS_FILE, index=False)

    if not os.path.exists(RESERVATIONS_FILE):
        pd.DataFrame(columns=[
            "owner", "customer_name", "email", "phone", "room_name",
            "check_in", "check_out", "guests", "total_price", "status"
        ]).to_csv(RESERVATIONS_FILE, index=False)


def read_csv(file):
    return pd.read_csv(file)


def save_csv(df, file):
    df.to_csv(file, index=False)


init_files()


# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "owner" not in st.session_state:
    st.session_state.owner = None


# ---------------- CSS ----------------
st.markdown("""
<style>
.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #1f2937;
}
.card {
    padding: 25px;
    border-radius: 14px;
    background-color: #f8fafc;
    border: 1px solid #e5e7eb;
}
.metric-card {
    padding: 20px;
    background-color: #ffffff;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ---------------- AUTH ----------------
def signup():
    st.subheader("Create Owner Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Signup"):
        owners = read_csv(OWNERS_FILE)

        if username == "" or password == "":
            st.error("Please fill all fields.")
        elif username in owners["username"].values:
            st.error("Username already exists.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            new_owner = pd.DataFrame([{
                "username": username,
                "password": hash_password(password)
            }])
            owners = pd.concat([owners, new_owner], ignore_index=True)
            save_csv(owners, OWNERS_FILE)
            st.success("Account created successfully. Please login now.")


def login():
    st.subheader("Owner Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        owners = read_csv(OWNERS_FILE)
        hashed = hash_password(password)

        match = owners[
            (owners["username"] == username) &
            (owners["password"] == hashed)
        ]

        if not match.empty:
            st.session_state.logged_in = True
            st.session_state.owner = username
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid username or password.")


# ---------------- PUBLIC BOOKING ----------------
def public_booking():
    hotels = read_csv(HOTELS_FILE)
    rooms = read_csv(ROOMS_FILE)

    st.markdown('<div class="main-title">🏨 Hotel Reservation System</div>', unsafe_allow_html=True)
    st.write("Book rooms easily and quickly.")

    if hotels.empty:
        st.warning("No hotel available yet.")
        return

    hotel_names = hotels["hotel_name"].tolist()
    selected_hotel = st.selectbox("Select Hotel", hotel_names)

    hotel = hotels[hotels["hotel_name"] == selected_hotel].iloc[0]
    owner = hotel["owner"]

    st.info(f"📍 Location: {hotel['location']} | ☎ Phone: {hotel['phone']}")

    hotel_rooms = rooms[
        (rooms["owner"] == owner) &
        (rooms["available"] == "Yes")
    ]

    if hotel_rooms.empty:
        st.warning("No available rooms for this hotel.")
        return

    room_names = hotel_rooms["room_name"].tolist()
    selected_room = st.selectbox("Select Room", room_names)

    room = hotel_rooms[hotel_rooms["room_name"] == selected_room].iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Room Type: **{room['room_type']}**")
    with col2:
        st.write(f"Price/Night: **${room['price']}**")

    st.divider()

    name = st.text_input("Customer Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    guests = st.number_input("Guests", min_value=1, max_value=10)

    check_in = st.date_input("Check-in Date", min_value=date.today())
    check_out = st.date_input("Check-out Date", min_value=date.today())

    if check_out > check_in:
        nights = (check_out - check_in).days
        total = nights * int(room["price"])
        st.success(f"Total Nights: {nights}")
        st.info(f"Total Price: ${total}")
    else:
        total = 0
        st.warning("Check-out date must be after check-in date.")

    if st.button("Confirm Booking"):
        if name and email and phone and check_out > check_in:
            reservations = read_csv(RESERVATIONS_FILE)

            new_booking = pd.DataFrame([{
                "owner": owner,
                "customer_name": name,
                "email": email,
                "phone": phone,
                "room_name": selected_room,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "total_price": total,
                "status": "Confirmed"
            }])

            reservations = pd.concat([reservations, new_booking], ignore_index=True)
            save_csv(reservations, RESERVATIONS_FILE)

            st.success("Booking confirmed successfully!")
        else:
            st.error("Please complete all fields correctly.")


# ---------------- OWNER DASHBOARD ----------------
def owner_dashboard():
    owner = st.session_state.owner

    st.sidebar.success(f"Logged in as: {owner}")

    menu = st.sidebar.radio(
        "Owner Dashboard",
        ["Dashboard", "Hotel Profile", "Manage Rooms", "Reservations", "Logout"]
    )

    if menu == "Dashboard":
        st.markdown('<div class="main-title">📊 Owner Dashboard</div>', unsafe_allow_html=True)

        hotels = read_csv(HOTELS_FILE)
        rooms = read_csv(ROOMS_FILE)
        reservations = read_csv(RESERVATIONS_FILE)

        my_rooms = rooms[rooms["owner"] == owner]
        my_res = reservations[reservations["owner"] == owner]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Rooms", len(my_rooms))

        with col2:
            st.metric("Total Reservations", len(my_res))

        with col3:
            revenue = my_res["total_price"].sum() if not my_res.empty else 0
            st.metric("Total Revenue", f"${revenue}")

    elif menu == "Hotel Profile":
        st.markdown('<div class="main-title">🏨 Hotel Profile</div>', unsafe_allow_html=True)

        hotels = read_csv(HOTELS_FILE)
        existing = hotels[hotels["owner"] == owner]

        hotel_name = st.text_input(
            "Hotel Name",
            value=existing.iloc[0]["hotel_name"] if not existing.empty else ""
        )

        location = st.text_input(
            "Location",
            value=existing.iloc[0]["location"] if not existing.empty else ""
        )

        phone = st.text_input(
            "Hotel Phone",
            value=existing.iloc[0]["phone"] if not existing.empty else ""
        )

        if st.button("Save Hotel Profile"):
            hotels = hotels[hotels["owner"] != owner]

            new_hotel = pd.DataFrame([{
                "owner": owner,
                "hotel_name": hotel_name,
                "location": location,
                "phone": phone
            }])

            hotels = pd.concat([hotels, new_hotel], ignore_index=True)
            save_csv(hotels, HOTELS_FILE)

            st.success("Hotel profile saved successfully.")

    elif menu == "Manage Rooms":
        st.markdown('<div class="main-title">🛏 Manage Rooms</div>', unsafe_allow_html=True)

        rooms = read_csv(ROOMS_FILE)

        with st.form("add_room_form"):
            room_name = st.text_input("Room Name / Number")
            room_type = st.selectbox("Room Type", ["Single", "Double", "Deluxe", "Suite"])
            price = st.number_input("Price per Night", min_value=1)
            available = st.selectbox("Available", ["Yes", "No"])

            submitted = st.form_submit_button("Add Room")

            if submitted:
                new_room = pd.DataFrame([{
                    "owner": owner,
                    "room_name": room_name,
                    "room_type": room_type,
                    "price": price,
                    "available": available
                }])

                rooms = pd.concat([rooms, new_room], ignore_index=True)
                save_csv(rooms, ROOMS_FILE)
                st.success("Room added successfully.")

        st.subheader("Your Rooms")
        my_rooms = rooms[rooms["owner"] == owner]
        st.dataframe(my_rooms, use_container_width=True)

    elif menu == "Reservations":
        st.markdown('<div class="main-title">📋 Reservations</div>', unsafe_allow_html=True)

        reservations = read_csv(RESERVATIONS_FILE)
        my_res = reservations[reservations["owner"] == owner]

        if my_res.empty:
            st.info("No reservations yet.")
        else:
            st.dataframe(my_res, use_container_width=True)

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.owner = None
        st.rerun()


# ---------------- MAIN APP ----------------
st.sidebar.title("Navigation")

if st.session_state.logged_in:
    owner_dashboard()
else:
    page = st.sidebar.radio("Go to", ["Book Room", "Owner Login", "Owner Signup"])

    if page == "Book Room":
        public_booking()
    elif page == "Owner Login":
        login()
    elif page == "Owner Signup":
        signup()
