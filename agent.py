# python
import pickle
from collections import UserDict
from datetime import datetime, timedelta


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __str__(self):
        return self.value.title()


class Phone(Field):
    def __init__(self, value):
        v = str(value).strip()
        if not (len(v) == 10 and v.isdigit()):
            raise ValueError("Incorrect phone number format.")
        super().__init__(v)


class Birthday(Field):
    def __init__(self, value):
        try:
            if isinstance(value, datetime):
                dt = value
            else:
                s = str(value).strip()
                if not s:
                    raise ValueError("Invalid date format. Use DD.MM.YYYY")
                dt = datetime.strptime(s, "%d.%m.%Y")
            super().__init__(dt)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def edit_phone(self, old_phone, new_phone):
        for i, phone in enumerate(self.phones):
            if phone.value == old_phone:
                self.phones[i] = Phone(new_phone)
                break

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def remove_phone(self, phone):
        for i, p in enumerate(self.phones):
            if p.value == phone:
                del self.phones[i]
                return True
        return False

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        birthday_str = f", birthday: {self.birthday.value.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{birthday_str}"


class AddressBook(UserDict):
    def __init__(self):
        super().__init__()

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        del self.data[name]

    def get_upcoming_birthdays(self) -> list[dict[str, str]]:
        """
        Generates a list of upcoming birthdays within the next 7 days for contacts
        in the address book, including adjusted congratulation dates when birthdays
        fall on a weekend. If a birthday occurs on a Saturday or Sunday, the
        congratulation date is moved to the next Monday.

        :return: A list of dictionaries, where each dictionary contains details about
                 an upcoming birthday. Each dictionary has the keys 'name'
                 (the contact's name) and 'congratulation_date' (a string representing
                 the adjusted congratulation date in 'DD.MM.YYYY' format).
        """
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            # Skip contacts without birthday
            if record.birthday is None:
                continue

            birthday = record.birthday.value.date()

            # Set birthday for current year
            birthday_this_year = birthday.replace(year=today.year)

            # If birthday has passed this year, consider next year
            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            # Calculate days until birthday
            days_until_birthday = (birthday_this_year - today).days

            # Check if birthday is within next 7 days (including today)
            # 0 - today, 1-6 - next 6 days, total 7 days
            if 0 <= days_until_birthday <= 6:
                # Set congratulation date
                congratulation_date = birthday_this_year

                # Check if birthday falls on weekend
                # weekday(): Monday=0, Tuesday=1, ..., Saturday=5, Sunday=6
                if congratulation_date.weekday() == 5:  # Saturday
                    # Move to Monday (add 2 days)
                    congratulation_date = congratulation_date + timedelta(days=2)
                elif congratulation_date.weekday() == 6:  # Sunday
                    # Move to Monday (add 1 day)
                    congratulation_date = congratulation_date + timedelta(days=1)

                # Add to list
                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                })

        return upcoming_birthdays


def save_data(book: AddressBook, filename: str = "addressbook.pkl"):
    """Serialize and save AddressBook to disk using pickle."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename: str = "addressbook.pkl") -> AddressBook:
    """Load AddressBook from disk or return a new one if file not found."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    """Decorator to handle input errors."""

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Invalid command format. Please provide all required arguments."
        except Exception as e:
            return f"An error occurred: {str(e)}"

    return inner


def parse_input(user_input):
    """Parse user input into command and arguments."""
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    """Add a new contact or add phone to existing contact."""
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    """Change phone number for existing contact."""
    if len(args) < 3:
        return "Please provide name, old phone, and new phone."

    name, old_phone, new_phone, *_ = args
    record = book.find(name)

    if record is None:
        return "Contact not found."

    # Check if old phone exists
    if record.find_phone(old_phone) is None:
        return f"Phone {old_phone} not found for contact {name}."

    record.edit_phone(old_phone, new_phone)
    return "Phone number updated."


@input_error
def show_phone(args, book: AddressBook):
    """Show phone numbers for a contact."""
    if len(args) < 1:
        return "Please provide a name."

    name, *_ = args
    record = book.find(name)

    if record is None:
        return "Contact not found."

    if not record.phones:
        return f"{name} has no phone numbers."

    phones = "; ".join(p.value for p in record.phones)
    return f"{name}: {phones}"


@input_error
def show_all(args, book: AddressBook):
    """Show all contacts in the address book."""
    if not book.data:
        return "Address book is empty."

    result = []
    for record in book.data.values():
        result.append(str(record))
    return "\n".join(result)


@input_error
def add_birthday(args, book: AddressBook):
    """Add birthday to a contact."""
    if len(args) < 2:
        return "Please provide name and birthday (DD.MM.YYYY)."

    name, birthday, *_ = args
    record = book.find(name)

    if record is None:
        return "Contact not found."

    record.add_birthday(birthday)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args, book: AddressBook):
    """Show birthday for a contact."""
    if len(args) < 1:
        return "Please provide a name."

    name, *_ = args
    record = book.find(name)

    if record is None:
        return "Contact not found."

    if record.birthday is None:
        return f"{name} has no birthday set."

    return f"{name}'s birthday: {record.birthday.value.strftime('%d.%m.%Y')}"


@input_error
def birthdays(args, book: AddressBook):
    """Show upcoming birthdays in the next 7 days."""
    upcoming = book.get_upcoming_birthdays()

    if not upcoming:
        return "No upcoming birthdays in the next 7 days."

    result = ["Upcoming birthdays:"]
    for entry in upcoming:
        result.append(f"{entry['name']}: {entry['congratulation_date']}")

    return "\n".join(result)


def main():
    book = load_data()
    print("Welcome to the assistant bot!")

    try:
        while True:
            user_input = input("Enter a command: ")
            command, *args = parse_input(user_input)

            if command in ["close", "exit"]:
                save_data(book)
                print("Good bye!")
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(show_phone(args, book))

            elif command == "all":
                print(show_all(args, book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(birthdays(args, book))

            else:
                print("Invalid command.")
    except (KeyboardInterrupt, EOFError):
        # Ensure data is saved on interrupt/EOF
        print("\nGood bye!")
        save_data(book)


if __name__ == "__main__":
    main()
