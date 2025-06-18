"""Command-line interface for the calculator."""

from typing import Tuple
from .calculator import Calculator


class CLI:
    """Command-line interface for the calculator."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.calculator = Calculator()

    def display_menu(self) -> None:
        """Shows available operations."""
        print("\nAvailable operations:")
        print("1. Add")
        print("2. Subtract")
        print("3. Multiply")
        print("4. Divide")
        print("5. Quit")

    def get_numbers(self) -> Tuple[float, float]:
        """Gets two numbers from user."""
        while True:
            try:
                num1 = float(input("Enter first number: "))
                num2 = float(input("Enter second number: "))
                return num1, num2
            except ValueError:
                print("Invalid input. Please enter valid numbers.")

    def run(self) -> None:
        """Main loop for interactive calculator."""
        print("Welcome to the Calculator!")
        
        while True:
            self.display_menu()
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '5':
                print("Thank you for using the calculator!")
                break
            
            if choice not in ['1', '2', '3', '4']:
                print("Invalid choice. Please try again.")
                continue

            try:
                num1, num2 = self.get_numbers()
                
                if choice == '1':
                    result = self.calculator.add(num1, num2)
                    print(f"{num1} + {num2} = {result}")
                elif choice == '2':
                    result = self.calculator.subtract(num1, num2)
                    print(f"{num1} - {num2} = {result}")
                elif choice == '3':
                    result = self.calculator.multiply(num1, num2)
                    print(f"{num1} * {num2} = {result}")
                elif choice == '4':
                    result = self.calculator.divide(num1, num2)
                    print(f"{num1} / {num2} = {result}")
                    
            except ZeroDivisionError as e:
                print(f"Error: {e}")
            except KeyboardInterrupt:
                raise