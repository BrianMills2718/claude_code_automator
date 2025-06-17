"""Command-line interface for the calculator."""

from typing import Optional, Union
from .calculator import Calculator


class CLI:
    """Command-line interface for the calculator."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.calculator = Calculator()

    def run(self) -> None:
        """Run the interactive calculator CLI."""
        print("Welcome to the Calculator!")
        print("Available operations: add, subtract, multiply, divide")
        print("Type 'quit' to exit.\n")

        while True:
            operation = input("Enter operation: ").strip().lower()
            
            if operation == 'quit':
                break
            
            if operation not in ['add', 'subtract', 'multiply', 'divide']:
                print("Invalid operation. Please try again.\n")
                continue

            try:
                num1 = self._get_number("Enter first number: ")
                num2 = self._get_number("Enter second number: ")
                
                result = self._perform_operation(operation, num1, num2)
                print(f"Result: {result}\n")
                
            except ValueError as e:
                print(f"Error: {e}\n")
            except KeyboardInterrupt:
                raise

    def _get_number(self, prompt: str) -> Union[int, float]:
        """Get a number from user input."""
        while True:
            try:
                value = input(prompt).strip()
                # Try int first, then float
                try:
                    return int(value)
                except ValueError:
                    return float(value)
            except ValueError:
                print("Invalid number. Please try again.")

    def _perform_operation(
        self, operation: str, num1: Union[int, float], num2: Union[int, float]
    ) -> Union[int, float]:
        """Perform the specified operation."""
        if operation == 'add':
            return self.calculator.add(num1, num2)
        elif operation == 'subtract':
            return self.calculator.subtract(num1, num2)
        elif operation == 'multiply':
            return self.calculator.multiply(num1, num2)
        elif operation == 'divide':
            return self.calculator.divide(num1, num2)
        else:
            raise ValueError(f"Unknown operation: {operation}")