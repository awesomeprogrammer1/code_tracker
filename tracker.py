import csv
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "problems.csv")

print(" Welcome to Code Tracker! This tool helps you keep track of your coding projects and progress." 
" Options: \n 1. Log Problem \n 2. View Progress \n 3. Exit")

option = input("Option: ")

if option == "1":
    problem_name = input("Enter the name of the problem: ")
    difficulty = input("Enter the difficulty level (Easy, Medium, Hard): ")
    time_spent = float(input("Enter the time spent (in hours): "))
    log_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="") as log_file:
        writer = csv.writer(log_file)
        writer.writerow([problem_name, difficulty, time_spent, log_date])
    print("Problem logged successfully!")
elif option == "2":
    if not os.path.exists(LOG_FILE):
        print("No problems logged yet.")
    else:
        with open(LOG_FILE, "r") as log_file:
            reader = csv.reader(log_file)
            problem_type = input("  \n What would you like to sort by? \n 1. Difficulty \n 2. Time Spent \n 3. Date Logged \n 4. View All Entries \n Option: ")
            if problem_type == "1":
                difficulty_filter = input("Filter by difficulty (Easy, Medium, Hard, All): ").strip().capitalize()
                if difficulty_filter == "All":
                    sorted_problems = sorted((x for x in reader if x), key=lambda x: x[1])
                else:
                    sorted_problems = sorted((x for x in reader if x and x[1] == difficulty_filter), key=lambda x: x[1])
                print(f"Logged Problems - {difficulty_filter}:")
                for row in sorted_problems:
                    print(f"Problem: {row[0]}, Difficulty: {row[1]}, Time Spent: {float(row[2])} hours, Date Logged: {row[3]}")
            elif problem_type == "2":
                sorted_problems = sorted((x for x in reader if x), key=lambda x: float(x[2]))
                print("Logged Problems Sorted by Time Spent:")
                for row in sorted_problems:
                    print(f"Problem: {row[0]}, Difficulty: {row[1]}, Time Spent: {float(row[2])} hours, Date Logged: {row[3]}")
            elif problem_type == "3":
                sorted_problems = sorted((x for x in reader if x), key=lambda x: datetime.strptime(x[3], "%Y-%m-%d %H:%M:%S"))
                print("Logged Problems Sorted by Date Logged:")
                for row in sorted_problems:
                    print(f"Problem: {row[0]}, Difficulty: {row[1]}, Time Spent: {float(row[2])} hours, Date Logged: {row[3]}")
            else:
                print("Logged Problems:")
                for row in reader:
                    print(f"Problem: {row[0]}, Difficulty: {row[1]}, Time Spent: {float(row[2])} hours, Date Logged: {row[3]}")