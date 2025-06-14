def greet(name):
    """Function that takes a name and prints a greeting message."""
    print(f"Hello, {name}! Welcome!")


def main():
    """Main function that demonstrates usage of the greet function."""
    # Demonstrate usage with different names
    greet("Alice")
    greet("Bob")
    greet("World")


if __name__ == "__main__":
    main()