import sys
from typing import Optional
from .weather_client import WeatherClient


class WeatherCLI:
    """Command-line interface for the weather application."""
    
    def __init__(self) -> None:
        self.weather_client = WeatherClient()
        self.running = True
    
    def display_menu(self) -> None:
        """Display the main menu."""
        print("\n" + "="*40)
        print("         WEATHER CLI")
        print("="*40)
        print("1. Check Weather")
        print("2. List Cities")
        print("3. Exit")
        print("="*40)
    
    def check_weather(self) -> None:
        """Handle checking weather for a city."""
        city = input("\nEnter city name: ").strip()
        if not city:
            print("City name cannot be empty!")
            return
        
        weather_data = self.weather_client.get_weather(city)
        
        if weather_data:
            print(f"\n🌤  Weather for {city.title()}:")
            print(f"   Temperature: {weather_data['temperature']}")
            print(f"   Conditions:  {weather_data['description']}")
        else:
            print(f"\n❌ Weather data not available for '{city}'")
            print("   Try one of the available cities (use option 2 to list)")
    
    def list_cities(self) -> None:
        """Display list of available cities."""
        cities = self.weather_client.get_available_cities()
        print("\n📍 Available cities:")
        for i, city in enumerate(cities, 1):
            print(f"   {i:2d}. {city}")
    
    def handle_choice(self, choice: str) -> None:
        """Handle user menu choice."""
        if choice == "1":
            self.check_weather()
        elif choice == "2":
            self.list_cities()
        elif choice == "3":
            print("\nThank you for using Weather CLI! Goodbye! 👋")
            self.running = False
        else:
            print("\n❌ Invalid choice! Please enter 1, 2, or 3.")
    
    def run(self) -> None:
        """Run the main CLI loop."""
        print("Welcome to Weather CLI! 🌦")
        
        while self.running:
            try:
                self.display_menu()
                choice = input("\nEnter your choice (1-3): ").strip()
                self.handle_choice(choice)
            except KeyboardInterrupt:
                print("\n\nInterrupted! Exiting...")
                break
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                print("Please try again.")


def main() -> None:
    """Entry point for the CLI."""
    cli = WeatherCLI()
    cli.run()


if __name__ == "__main__":
    main()