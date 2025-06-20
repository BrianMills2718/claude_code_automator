#!/usr/bin/env python3
"""CLI Calculator - A command-line calculator with basic arithmetic operations."""

import argparse
import sys
from typing import NoReturn


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="CLI Calculator - Perform basic arithmetic operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py add 5 3
  python main.py subtract 10 4
  python main.py multiply 6 7
  python main.py divide 20 5
        """
    )
    
    # Create subparsers for each operation
    subparsers = parser.add_subparsers(
        dest='operation',
        help='The arithmetic operation to perform',
        required=True
    )
    
    # Add subcommand
    add_parser = subparsers.add_parser('add', help='Add two numbers')
    add_parser.add_argument('num1', type=float, help='First number')
    add_parser.add_argument('num2', type=float, help='Second number')
    
    # Subtract subcommand
    sub_parser = subparsers.add_parser('subtract', help='Subtract second number from first')
    sub_parser.add_argument('num1', type=float, help='First number')
    sub_parser.add_argument('num2', type=float, help='Second number')
    
    # Multiply subcommand
    mul_parser = subparsers.add_parser('multiply', help='Multiply two numbers')
    mul_parser.add_argument('num1', type=float, help='First number')
    mul_parser.add_argument('num2', type=float, help='Second number')
    
    # Divide subcommand
    div_parser = subparsers.add_parser('divide', help='Divide first number by second')
    div_parser.add_argument('num1', type=float, help='First number (dividend)')
    div_parser.add_argument('num2', type=float, help='Second number (divisor)')
    
    return parser


def main() -> None:
    """Main entry point for the CLI calculator."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Map operations to functions
        operations = {
            'add': add,
            'subtract': subtract,
            'multiply': multiply,
            'divide': divide
        }
        
        # Get the operation function
        operation_func = operations[args.operation]
        
        # Perform the calculation
        result = operation_func(args.num1, args.num2)
        
        # Print the result
        print(result)
        
    except ZeroDivisionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()