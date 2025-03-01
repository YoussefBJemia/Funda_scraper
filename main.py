import asyncio
import sys
import os

# Import components
from Interface.interface import show_startup_screen
from Scraper.pipeline import FundaScraperPipeline




async def run_pipeline():
    """Run the scraper pipeline asynchronously."""
    scraper = FundaScraperPipeline()
    await scraper.run()

def main():
    """Main entry point for the application."""
    # Display the startup screen from interface.py
    user_choice_continue = show_startup_screen()

    # If the user canceled, exit the program
    if not user_choice_continue:
        print("\n\nScraping canceled by user. Exiting...")
        sys.exit(0)
    
    # Run the pipeline asynchronously
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nAn error occurred: {str(e)}")
        sys.exit(1)

# Entry point for execution
if __name__ == "__main__":
    main()