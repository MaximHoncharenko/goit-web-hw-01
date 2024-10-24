from abc import ABC, abstractmethod
from collections import UserDict
from datetime import datetime, timedelta

# Абстрактний базовий клас для уявлень
class UserView(ABC):

    @abstractmethod
    def display_message(self, message):
        pass

    @abstractmethod
    def display_contacts(self, contacts):
        pass

    @abstractmethod
    def display_commands(self):
        pass

# Конкретний клас для консольного інтерфейсу
class ConsoleView(UserView):
    def display_message(self, message):
        print(message)

    def display_contacts(self, contacts):
        if not contacts:
            print("Адресна книга порожня.")
        else:
            for name, record in contacts.items():
                phones = record.show_phones()
                birthday = record.show_birthday() if record.birthday else "Не встановлено"
                print(f"{name}: Телефони: {phones}, День народження: {birthday}")

    def display_commands(self):
        print("""
Доступні команди:
1. add <name> <phone> - Додати контакт
2. change <name> <old_phone> <new_phone> - Змінити телефон контакту
3. phone <name> - Показати телефони контакту
4. add-birthday <name> <birthday> - Додати день народження
5. show-birthday <name> - Показати день народження
6. birthdays - Показати найближчі дні народження
7. all - Показати всі контакти
8. exit - Вихід
        """)

# Клас для зберігання полів
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Неправильний формат номера телефону")
        super().__init__(value)

    @staticmethod
    def validate(value):
        return len(value) == 10 and value.isdigit()

class Birthday(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Неправильний формат дати. Використовуйте формат: ДД.ММ.РРРР")
        super().__init__(value)

    @staticmethod
    def validate(value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            return True
        except ValueError:
            return False

# Клас Record для записів
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        new_phone = Phone(phone)
        if new_phone not in self.phones:
            self.phones.append(new_phone)

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return f"Телефон {phone} видалено"
        return f"Телефон {phone} не знайдено"

    def edit_phone(self, old_phone, new_phone):
        if not Phone.validate(new_phone):
            raise ValueError("Некоректний формат нового номера телефону")
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return f"Телефон {old_phone} змінено на {new_phone}"
        return f"Телефон {old_phone} не знайдено"

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def show_phones(self):
        return ', '.join(phone.value for phone in self.phones)

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def show_birthday(self):
        if self.birthday:
            return self.birthday.value
        return "День народження не встановлено"

    def get_days_to_birthday(self):
        if self.birthday:
            today = datetime.now().date()
            birthday_this_year = datetime.strptime(self.birthday.value, "%d.%m.%Y").replace(year=today.year).date()
            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)
            return (birthday_this_year - today).days
        return None

# Клас AddressBook для зберігання контактів
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.now().date()
        upcoming_birthdays = []
        for record in self.data.values():
            days_to_birthday = record.get_days_to_birthday()
            if days_to_birthday is not None and 0 <= days_to_birthday <= 7:
                birthday_date = today + timedelta(days=days_to_birthday)
                if birthday_date.weekday() >= 5:  # якщо субота або неділя
                    birthday_date += timedelta(days=(7 - birthday_date.weekday()))  # перенос на понеділок
                upcoming_birthdays.append({"name": record.name.value, "birthday": birthday_date.strftime("%d.%m.%Y")})
        return upcoming_birthdays

# Функції-обробники команд
def add_contact(args, book: AddressBook, view: UserView):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    view.display_message(message)

def change_phone(args, book: AddressBook, view: UserView):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        message = record.edit_phone(old_phone, new_phone)
    else:
        message = f"Контакт {name} не знайдено"
    view.display_message(message)

def show_phone(args, book: AddressBook, view: UserView):
    name = args[0]
    record = book.find(name)
    if record:
        message = f"Телефони {name}: {record.show_phones()}"
    else:
        message = f"Контакт {name} не знайдено"
    view.display_message(message)

def show_all(book: AddressBook, view: UserView):
    view.display_contacts(book.data)

def add_birthday(args, book: AddressBook, view: UserView):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        message = f"День народження для {name} встановлено: {birthday}"
    else:
        message = f"Контакт {name} не знайдено"
    view.display_message(message)

def birthdays(book: AddressBook, view: UserView):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if upcoming_birthdays:
        message = "\n".join([f"{item['name']} - {item['birthday']}" for item in upcoming_birthdays])
    else:
        message = "Немає днів народження на наступному тижні"
    view.display_message(message)

# Основна функція з вибором уявлення
def main():
    book = AddressBook()
    view = ConsoleView()
    
    view.display_message("Welcome to the assistant bot!")
    view.display_commands()
    
    while True:
        user_input = input("Enter a command: ")
        command, *args = user_input.split()

        if command in ["close", "exit"]:
            view.display_message("Good bye!")
            break

        elif command == "hello":
            view.display_message("How can I help you?")

        elif command == "add":
            add_contact(args, book, view)

        elif command == "change":
            change_phone(args, book, view)

        elif command == "phone":
            show_phone(args, book, view)

        elif command == "all":
            show_all(book, view)

        elif command == "add-birthday":
            add_birthday(args, book, view)

        elif command == "birthdays":
            birthdays(book, view)

        else:
            view.display_message("Invalid command.")

if __name__ == "__main__":
    main()
