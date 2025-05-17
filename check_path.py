import sys
import os

print("Python Path:")
for path in sys.path:
    print(f"  - {path}")

print("\nCurrent Directory:", os.getcwd())
print("\nChecking if llm directory exists:", os.path.exists("llm"))

try:
    import llm
    print("\nSuccessfully imported llm module!")
    print("llm.__file__:", llm.__file__)
except ImportError as e:
    print(f"\nFailed to import llm module: {e}") 