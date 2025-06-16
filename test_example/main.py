#!/usr/bin/env python3
"""Command-line calculator with basic arithmetic operations."""

from src.calculator import add, subtract, multiply, divide


def get_number(prompt: str) -> float:
    """Get a number from user input with error handling.
    
    Args:
        prompt: The prompt to display to the user
        
    Returns:
        The number entered by the user
        
    Raises:
        ValueError: If input cannot be converted to float
    """
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def get_operation() -> str:
    """Get operation choice from user.
    
    Returns:
        Single character representing the operation
    """
    print("\nAvailable operations:")
    print("+ : Addition")
    print("- : Subtraction")
    print("* : Multiplication")
    print("/ : Division")
    print("q : Quit")
    
    while True:
        operation = input("\nSelect operation (+, -, *, /, q): ").strip()
        if operation in ['+', '-', '*', '/', 'q']:
            return operation
        print("Invalid operation. Please choose +, -, *, /, or q")


def perform_calculation(num1: float, num2: float, operation: str) -> float:
    """Perform the calculation based on operation.
    
    Args:
        num1: First number
        num2: Second number
        operation: Operation to perform
        
    Returns:
        Result of the calculation
        
    Raises:
        ValueError: If division by zero or invalid operation
    """
    if operation == '+':
        return add(num1, num2)
    elif operation == '-':
        return subtract(num1, num2)
    elif operation == '*':
        return multiply(num1, num2)
    elif operation == '/':
        return divide(num1, num2)
    else:
        raise ValueError(f"Invalid operation: {operation}")


def main() -> None:
    """Main calculator program loop."""
    print("Welcome to Python Calculator!")
    print("This calculator supports basic arithmetic operations.")
    
    while True:
        try:
            operation = get_operation()
            
            if operation == 'q':
                print("Thank you for using Python Calculator!")
                break
            
            num1 = get_number("Enter first number: ")
            num2 = get_number("Enter second number: ")
            
            result = perform_calculation(num1, num2, operation)
            print(f"\nResult: {num1} {operation} {num2} = {result}")
            
        except ValueError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()