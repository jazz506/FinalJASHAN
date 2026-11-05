"""
File Name   : langham_hotel_management.py
Author      : Jashanpreet Kaur
Course      : BBIM502 Introduction to Programming - Assessment 2 (Project)
Description : Console-based Hotel Management System for LANGHAM Hotels.
              Re-written in Python from the original C# prototype.
              Menu options:
                1 Add Room                 6 Billing & De-Allocation
                2 Delete Room              7 Save Room Allocation to File
                3 Display Room Details     8 Display Room Allocation from File
                4 Allocate Room            9 Backup and Clear Allocation File
                5 Display Allocation       0 Exit
Date        : 01/11/2026
"""

# ---------------------------------------------------------------------------
# Imports (ImportError handling)
# ---------------------------------------------------------------------------
import os
import ast
import math
from datetime import datetime

# Optional module: 'tabulate' gives nicer tables. If it is not installed the
# program falls back to plain formatting instead of crashing (ImportError).
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants (UPPER_SNAKE_CASE) - change STUDENT_ID to your real student ID
# ---------------------------------------------------------------------------
STUDENT_ID = "00000000"
DATA_FILE = f"LHMS_{STUDENT_ID}.txt"
GST_RATE = 0.15            # New Zealand GST (15%)
MAX_NIGHTS = 365           # Longest booking allowed

# ---------------------------------------------------------------------------
# Global data (list of dictionaries - one dictionary per room)
# ---------------------------------------------------------------------------
rooms = [
    {"room_no": 101, "room_type": "Single", "rate": 180.0,
     "features": "1 single bed, city view, Wi-Fi",
     "customer": None, "nights": 0},
    {"room_no": 102, "room_type": "Double", "rate": 260.0,
     "features": "1 queen bed, harbour view, minibar",
     "customer": None, "nights": 0},
    {"room_no": 201, "room_type": "Suite", "rate": 450.0,
     "features": "King bed, lounge, bath tub, balcony",
     "customer": None, "nights": 0},
]


# ===========================================================================
# Helper functions
# ===========================================================================
def safe_input(prompt):
    """Read a line from the user. Handles EOFError (input stream closed)."""
    try:
        return input(prompt).strip()
    except EOFError:
        # EOFError: no more input is available (e.g. Ctrl+D / piped input ended)
        print("\nInput stream closed. Exiting safely.")
        raise SystemExit(0)


def read_int(prompt, minimum=None, maximum=None):
    """Keep asking until a valid whole number in range is entered."""
    while True:
        text = safe_input(prompt)
        try:
            value = int(text)                       # may raise ValueError
            if minimum is not None and value < minimum:
                raise ValueError(f"must be at least {minimum}")
            if maximum is not None and value > maximum:
                raise ValueError(f"must be at most {maximum}")
            return value
        except ValueError as error:
            print(f"  Invalid number ({error}). Please try again.")


def read_float(prompt, minimum=0.0):
    """Keep asking until a valid positive decimal number is entered."""
    while True:
        text = safe_input(prompt)
        try:
            value = float(text)                     # may raise ValueError
            if value <= minimum:
                raise ValueError(f"must be greater than {minimum}")
            return value
        except ValueError as error:
            print(f"  Invalid amount ({error}). Please try again.")


def find_room(room_no):
    """Return the room dictionary for room_no, or None when not found."""
    for room in rooms:
        if room["room_no"] == room_no:
            return room
    return None


def is_allocated(room):
    """A room is allocated when it has a customer name."""
    return room["customer"] is not None


def print_table(headers, table_rows):
    """Display data as a table (uses tabulate if the import succeeded)."""
    if TABULATE_AVAILABLE:
        print(tabulate(table_rows, headers=headers, tablefmt="grid"))
        return
    print(" | ".join(f"{h:<14}" for h in headers))
    print("-" * (17 * len(headers)))
    for row in table_rows:
        print(" | ".join(f"{str(cell):<14}" for cell in row))


def parse_discount(text):
    """
    Convert a discount entered by the user (e.g. '10') into a number.
    SyntaxError  -> text is not valid Python syntax (e.g. '10 +')
    ValueError   -> text is valid syntax but not a plain number
    """
    try:
        value = ast.literal_eval(text)              # may raise SyntaxError/ValueError
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError("discount must be a number")
        if not 0 <= value <= 100:
            raise ValueError("discount must be between 0 and 100")
        return float(value)
    except SyntaxError:
        print("  Syntax error in discount entry - no discount applied.")
    except ValueError as error:
        print(f"  Invalid discount ({error}) - no discount applied.")
    return 0.0


# ===========================================================================
# Menu option functions
# ===========================================================================
def add_room():
    """Menu 1 - add a new room to the list."""
    print("\n--- Add Room ---")
    room_no = read_int("Room number (e.g. 301): ", minimum=1)

    # FIX 1 (Logical error): the original version allowed duplicate room numbers.
    if find_room(room_no) is not None:
        print(f"  Room {room_no} already exists. Room not added.")
        return

    room_type = safe_input("Room type (Single/Double/Suite): ").title()
    if room_type not in ("Single", "Double", "Suite"):
        print("  Invalid room type. Room not added.")
        return

    # FIX 2 (Logical error): negative / zero rates were accepted before.
    rate = read_float("Rate per night (NZD): ")
    features = safe_input("Features (short description): ")

    rooms.append({"room_no": room_no, "room_type": room_type, "rate": rate,
                  "features": features or "Not specified",
                  "customer": None, "nights": 0})
    print(f"  Room {room_no} added successfully.")


def delete_room():
    """Menu 2 - delete a room from the list."""
    print("\n--- Delete Room ---")
    room_no = read_int("Room number to delete: ", minimum=1)
    room = find_room(room_no)

    if room is None:
        print("  Room not found.")
    elif is_allocated(room):
        # FIX 3 (Logical error): rooms with a guest could be deleted before.
        print("  Room is currently allocated. Bill the guest first.")
    else:
        rooms.remove(room)
        print(f"  Room {room_no} deleted.")


def display_room_details():
    """Menu 3 - show room features before booking."""
    print("\n--- Room Details ---")
    if not rooms:
        print("  No rooms available in the system.")
        return
    table_rows = [[r["room_no"], r["room_type"], f"${r['rate']:.2f}",
                   "Occupied" if is_allocated(r) else "Vacant", r["features"]]
                  for r in rooms]
    print_table(["Room", "Type", "Rate", "Status", "Features"], table_rows)


def allocate_room():
    """Menu 4 - book a vacant room for a customer."""
    print("\n--- Allocate Room ---")
    vacant_rooms = [r for r in rooms if not is_allocated(r)]
    if not vacant_rooms:
        print("  No vacant rooms available.")
        return

    for position, room in enumerate(vacant_rooms, start=1):
        print(f"  {position}. Room {room['room_no']} ({room['room_type']}) "
              f"- ${room['rate']:.2f} per night")

    choice = read_int("Choose a room by list number: ")
    try:
        room = vacant_rooms[choice - 1]             # may raise IndexError
        if choice < 1:
            # Negative numbers would silently pick from the end of the list.
            raise IndexError("list number must be 1 or more")
    except IndexError:
        # IndexError: the chosen list number is outside the list
        print("  That list number is not on the list.")
        return

    customer = safe_input("Customer name: ")
    if not customer:
        # FIX 4 (Logical error): empty names produced "ghost" bookings.
        print("  Customer name cannot be blank.")
        return

    room["customer"] = customer.title()
    room["nights"] = read_int(f"Number of nights (1-{MAX_NIGHTS}): ", 1, MAX_NIGHTS)
    print(f"  Room {room['room_no']} allocated to {room['customer']}.")


def display_allocation_details():
    """Menu 5 - show current allocation status."""
    print("\n--- Room Allocation Details ---")
    allocated = [r for r in rooms if is_allocated(r)]
    if not allocated:
        print("  No rooms are currently allocated.")
        return
    table_rows = [[r["room_no"], r["room_type"], r["customer"], r["nights"]]
                  for r in allocated]
    print_table(["Room", "Type", "Customer", "Nights"], table_rows)


def calculate_bill(room, discount_percent):
    """
    Work out the bill for a room.
    Returns (subtotal, discount, gst, total, average_per_night).
    """
    # TypeError is raised if the rate or nights were stored as the wrong type
    # (e.g. None + number) - handled by the caller.
    base_amount = room["rate"] * room["nights"]

    # Demand surcharge: 0.1% compounded for every night booked.
    # OverflowError would occur if the numbers became too large for a float.
    try:
        surcharge = float(1.001) ** room["nights"]
    except OverflowError:
        print("  Surcharge too large to calculate - standard rate used.")
        surcharge = 1.0

    subtotal = base_amount * surcharge
    discount = subtotal * discount_percent / 100
    gst = (subtotal - discount) * GST_RATE
    total = subtotal - discount + gst

    # FIX 5 (Runtime error): nights = 0 caused ZeroDivisionError here.
    try:
        average_per_night = total / room["nights"]
    except ZeroDivisionError:
        average_per_night = 0.0
    return subtotal, discount, gst, total, average_per_night


def billing_and_deallocation():
    """Menu 6 - generate the bill and release the room."""
    global last_bill_total
    print("\n--- Billing & De-Allocation ---")
    room_no = read_int("Room number to check out: ", minimum=1)
    room = find_room(room_no)

    if room is None:
        print("  Room not found.")
        return
    if not is_allocated(room):
        print("  That room is not allocated.")
        return

    discount_percent = parse_discount(safe_input("Discount % (Enter for none): ") or "0")

    try:
        subtotal, discount, gst, total, average = calculate_bill(room, discount_percent)
    except TypeError as error:
        print(f"  Bill could not be calculated - bad data type ({error}).")
        return

    print("\n  ======== LANGHAM HOTELS - INVOICE ========")
    print(f"  Customer : {room['customer']}")
    print(f"  Room     : {room['room_no']} ({room['room_type']})")
    print(f"  Nights   : {room['nights']} @ ${room['rate']:.2f}")
    print(f"  Subtotal : ${subtotal:,.2f}")
    print(f"  Discount : -${discount:,.2f} ({discount_percent:.0f}%)")
    print(f"  GST (15%): ${gst:,.2f}")
    print(f"  TOTAL    : ${total:,.2f}")
    print(f"  Average per night: ${average:,.2f}")
    print("  ==========================================")

    last_bill_total = total                           # defined only after a bill
    room["customer"] = None                           # de-allocate the room
    room["nights"] = 0
    print(f"  Room {room_no} is now vacant.")


def build_allocation_lines():
    """Create the text lines that are saved to the file (menu 7)."""
    stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    lines = [f"--- Allocation snapshot saved {stamp} ---"]
    allocated = [r for r in rooms if is_allocated(r)]
    if not allocated:
        lines.append("No rooms allocated.")
    for r in allocated:
        lines.append(f"Room {r['room_no']} | {r['room_type']} | "
                     f"{r['customer']} | {r['nights']} night(s) | ${r['rate']:.2f}")
    return lines


def save_allocation_to_file():
    """Menu 7 - save allocation data to LHMS_<StudentID>.txt."""
    print("\n--- Save Room Allocation to File ---")
    try:
        # "a" creates the file if it does not exist, otherwise adds to the end.
        with open(DATA_FILE, "a", encoding="utf-8") as file:
            for line in build_allocation_lines():
                file.write(line + "\n")
        # The 'with' block closes the file automatically.
        print(f"  Data saved to {DATA_FILE}.")
    except IOError as error:
        print(f"  Could not write to the file: {error}")


def display_allocation_from_file():
    """Menu 8 - read the file and display its content."""
    print("\n--- Room Allocation From File ---")
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            content = file.read()
        print(content if content.strip() else "  The file is empty.")
    except FileNotFoundError:
        # FIX 6 (Runtime error): the program crashed when the file was missing.
        print(f"  {DATA_FILE} was not found. Use option 7 to create it first.")
    except IOError as error:
        print(f"  The file could not be opened: {error}")


def backup_and_clear_file():
    """Menu 9 - append content to a time-stamped backup, then empty the file."""
    print("\n--- Backup and Clear Allocation File ---")
    backup_name = (f"LHMS_{STUDENT_ID}_Backup_"
                   f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as source:
            content = source.read()
        with open(backup_name, "a", encoding="utf-8") as backup:
            backup.write(content)
        with open(DATA_FILE, "w", encoding="utf-8"):
            pass                                      # "w" empties the file
        print(f"  Backup created: {backup_name}")
        print(f"  {DATA_FILE} has been cleared.")
    except FileNotFoundError:
        print(f"  {DATA_FILE} does not exist - nothing to back up.")
    except IOError as error:
        print(f"  File operation failed: {error}")


def exit_application():
    """Menu 0 - show a closing summary and end the program."""
    try:
        print(f"\nLast bill total this session: ${last_bill_total:,.2f}")
    except NameError:
        # NameError: last_bill_total only exists after a bill was generated.
        print("\nNo bills were generated this session.")
    print("Thank you for using the LANGHAM Hotel Management System. Goodbye!")


# ===========================================================================
# Main menu
# ===========================================================================
def show_menu():
    """Print the application menu."""
    print("\n" + "=" * 46)
    print("      LANGHAM HOTEL MANAGEMENT SYSTEM")
    print("=" * 46)
    print(" 1. Add Room")
    print(" 2. Delete Room")
    print(" 3. Display Room Details")
    print(" 4. Allocate Room")
    print(" 5. Display Room Allocation Details")
    print(" 6. Billing & De-Allocation")
    print(" 7. Save Room Allocation to File")
    print(" 8. Display Room Allocation from File")
    print(" 9. Backup and Clear Allocation File")
    print(" 0. Exit")
    print("=" * 46)


def main():
    """Run the menu loop until the user chooses 0."""
    actions = {1: add_room, 2: delete_room, 3: display_room_details,
               4: allocate_room, 5: display_allocation_details,
               6: billing_and_deallocation, 7: save_allocation_to_file,
               8: display_allocation_from_file, 9: backup_and_clear_file}
    while True:
        show_menu()
        # FIX 7 (Runtime error): typing letters used to crash the menu.
        choice = read_int("Enter your choice (0-9): ", 0, 9)
        if choice == 0:
            exit_application()
            break
        actions[choice]()


if __name__ == "__main__":
    main()
