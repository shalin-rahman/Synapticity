# Overview

This guide explains how to create a simple Python "Hello, World!" application. The app will display "Hello, World!" in the console and allow for customization of the output message.

# Setup

1. **Install Python:** Ensure you have Python installed on your system. You can download it from [python.org](https://www.python.org/downloads/).
2. **Create a New File:** Open your favorite text editor or IDE and create a new file named `hello_world.py`.
3. **Copy the Code:** Copy the provided code snippet into the `hello_world.py` file.

# How it Works

The application consists of a single Python script that outputs "Hello, World!" to the console. Here’s how it works:

1. **Import Modules:** The script imports the `sys` and `time` modules.
2. **Main Function:** The `main()` function is defined to encapsulate the logic.
3. **Timer Start:** The timer starts before any operations are performed.
4. **Custom Message:** It checks if a command-line argument is provided. If not, it defaults to "World".
5. **Output Greeting:** The script prints the greeting message using an f-string.
6. **Execution Time:** The timer stops after the output and calculates the execution time in milliseconds.

# Security

This application is read-only and does not involve any sensitive data. It is designed for educational purposes and does not require any security measures.

# Running the Application

To run the application, open your terminal or command prompt and navigate to the directory where `hello_world.py` is located. Execute the following command:

```sh
python hello_world.py [Name]
```

Replace `[Name]` with the name you want to customize the message for (e.g., `John`). If no argument is provided, it will default to "World".

Example:
```sh
python hello_world.py John
```

Output:
```
Hello, John!
Execution Time: 0.12 ms
```

This guide should help anyone set up and run a basic Python "Hello, World!" application without any complexity or jargon.