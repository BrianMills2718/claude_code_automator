# User Journey Validation Report

**Total Journeys**: 3
**Passed**: 1
**Failed**: 2

## fetch_then_analyze - ❌ FAILED
**Description**: User fetches data then analyzes it
**Commands**:
  - `python main.py fetch AAPL`
  - `python main.py analyze AAPL`
**Errors**:
  - Step 2: Found forbidden pattern 'No data found'

## search_then_fetch - ❌ FAILED
**Description**: User searches for symbol then fetches it
**Commands**:
  - `python main.py search apple`
  - `python main.py fetch AAPL`
**Errors**:
  - Step 1: Found forbidden pattern 'No results found'
  - Expected pattern 'Search Results' not found in any output

## help_navigation - ✅ PASSED
**Description**: User explores help and available commands
**Commands**:
  - `python main.py --help`
  - `python main.py fetch --help`
