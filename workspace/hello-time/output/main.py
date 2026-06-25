import sys
import time

def main():
    # Start the timer
    start_time = time.time()

    # Get the custom message from command-line arguments
    name = "World" if len(sys.argv) == 1 else sys.argv[1]

    # Output the greeting message
    print(f"Hello, {name}!")

    # Calculate and print the execution time
    end_time = time.time()
    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"Execution Time: {execution_time:.2f} ms")

if __name__ == "__main__":
    main()
