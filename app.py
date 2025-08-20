from model import (session, engine, Base, Product)
from datetime import date, datetime
import csv


def menu():
    print("\nInventory Menu:")
    print("v) View a single product's inventory")
    print("a) Add a new product to the database")
    print("b) Make a backup of the entire inventory")
    return input("Enter your choice (v, a, b): ").strip().lower()


def view_product():
    while True:
        try:
            prod_id = int(input("Enter the product ID: "))
            product = session.query(Product).filter_by(
                product_id=prod_id).one_or_none()
            if product:
                print(f"\nID: {product.product_id}")
                print(f"Name: {product.product_name}")
                print(f"Quantity: {product.product_quantity}")
                print(f"Price: ${product.product_price / 100:.2f}")
                print(f"Last Updated: {product.date_updated}")
                break
            else:
                print("Product not found. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a valid product ID.")


def add_product():
    name = input("Enter product name: ").strip()
    while True:
        try:
            qty = int(input("Enter product quantity: "))
            break
        except ValueError:
            print("Please enter a valid integer for quantity.")
    while True:
        price_input = input("Enter product price (e.g., $4.99): ").strip()
        try:
            price = clean_price(price_input)
            break
        except Exception:
            print("Please enter a valid price (e.g., $4.99).")
    date_updated = date.today().strftime("%m/%d/%Y")
    row = [name, f"${price/100:.2f}",
           str(qty), date_updated]
    upsert_product_from_row(row)
    print("Product added/updated successfully.")


def backup_inventory():
    products = session.query(Product).all()
    with open("backup.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(
            ["product_name", "product_price", "product_quantity", "date_updated"])
        for p in products:
            writer.writerow([
                p.product_name,
                f"${p.product_price / 100:.2f}",
                p.product_quantity,
                datetime.strptime(
                    p.date_updated, "%Y-%m-%d").strftime("%m/%d/%Y")
            ])
    print("Backup completed: backup.csv")


def clean_data(value, data_type, type=None):
    if data_type == 'qty':
        return clean_qty(value)
    elif data_type == 'price':
        return clean_price(value)


def clean_qty(value):
    return int(value)


def clean_price(value):
    return int(float(value.replace('$', '')) * 100)


def upsert_product_from_row(row):
    product_name = row[0]
    product_price = clean_data(row[1], 'price')
    product_quantity = clean_data(row[2], 'qty')
    date_updated = datetime.strptime(row[3], "%m/%d/%Y").date()

    product = session.query(Product).filter(
        Product.product_name == product_name).one_or_none()

    if product is None:
        # Insert new product
        product = Product(
            product_name=product_name,
            product_quantity=product_quantity,
            product_price=product_price,
            date_updated=date_updated
        )
        session.add(product)
    else:
        # Update only if the new date is more recent
        old_date = datetime.strptime(product.date_updated, "%Y-%m-%d").date()
        # Need to do this comparison with time as well
        if date_updated >= old_date:
            product.product_quantity = product_quantity
            product.product_price = product_price
            product.date_updated = date_updated

    session.commit()


if __name__ == "__main__":
    # This will create inventory.db and all tables defined in Base's subclasses
    Base.metadata.create_all(engine)

    with open('./store-inventory/store-inventory/inventory.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            upsert_product_from_row(row)

    while True:
        choice = menu()
        if choice == 'v':
            view_product()
        elif choice == 'a':
            add_product()
        elif choice == 'b':
            backup_inventory()
        else:
            print('\nInvalid choice. Please enter v, a, or b.')
