#!/usr/bin/env python3
"""Command-line calculator with basic arithmetic operations."""

import sys
from typing import Optional

from src.calculator import Calculator


def get_number(prompt: str) -> Optional[float]:
    """Get a number from user input.

    Args:
        prompt: Message to display to user

    Returns:
        Float value entered by user, or None if invalid
    """
    try:
        return float(input(prompt))
    except ValueError:
        print("Invalid number. Please enter a valid number.")
        return None


def display_menu() -> None:
    """Display the calculator menu."""
    print("\n=== Python Calculator ===")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")
    print("5. Exit")
    print("========================")


def main() -> int:
    """Main calculator loop."""
    calculator = Calculator()

    print("Welcome to Python Calculator!")
    print("This calculator supports basic arithmetic operations.")

    while True:
        display_menu()

        choice = input("\nSelect operation (1-5): ").strip()

        if choice == '5':
            print("Thank you for using Python Calculator!")
            return 0

        if choice not in ['1', '2', '3', '4']:
            print("Invalid choice. Please select 1-5.")
            continue

        # Get operands
        num1 = get_number("Enter first number: ")
        if num1 is None:
            continue

        num2 = get_number("Enter second number: ")
        if num2 is None:
            continue

        # Perform operation
        try:
            if choice == '1':
                result = calculator.add(num1, num2)
                operation = "+"
            elif choice == '2':
                result = calculator.subtract(num1, num2)
                operation = "-"
            elif choice == '3':
                result = calculator.multiply(num1, num2)
                operation = "*"
            elif choice == '4':
                result = calculator.divide(num1, num2)
                operation = "/"

            # Display result
            print(f"\nResult: {num1} {operation} {num2} = {result}")

        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    sys.exit(main())
