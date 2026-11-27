import sys
from parser import parse_input

def main():
    if len(sys.argv) > 1:
        result = parse_input(sys.argv[1])
        print(f"Parsed: {result}")
    else:
        print("Usage: python main.py <input>")

if __name__ == "__main__":
    main()
