import csv
import os
from datetime import datetime
LOG_FILE = os.path.join(os.path.dirname(__file__), "todos.csv")

print("Welcome to To-Do Tracker! This tool helps you keep track of your to-dos."
" Options: \n 1. Log a New To-Do \n 2. View To-Dos \n 3. Remove a To-Do")

option = input("Option: ")

if option == "1":
    todo_name = input("Enter the to-do: ")
    difficulty = input("Enter the difficulty (Easy, Medium, Hard): ")
    log_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="") as log_file:
        writer = csv.writer(log_file)
        writer.writerow([todo_name, difficulty, log_date, "Pending"])
    print("To-do logged successfully!")

elif option == "2":
    if not os.path.exists(LOG_FILE):
        print("No to-dos logged yet.")
    else:
        with open(LOG_FILE, "r") as log_file:
            reader = csv.reader(log_file)
            view_type = input("\nWhat would you like to do? \n 1. Filter by Difficulty \n 2. Sort by Date Submitted \n 3. View All \n 4. Mark a To-Do as Done \n Option: ")
            if view_type == "1":
                difficulty_filter = input("Filter by difficulty (Easy, Medium, Hard, All): ").strip().capitalize()
                if difficulty_filter == "All":
                    todos = sorted((x for x in reader if x), key=lambda x: x[1])
                else:
                    todos = sorted((x for x in reader if x and x[1] == difficulty_filter), key=lambda x: x[1])
                print(f"To-Dos - {difficulty_filter}:")
                for row in todos:
                    print(f"To-Do: {row[0]}, Difficulty: {row[1]}, Date Submitted: {row[2]}, Status: {row[3]}")
            elif view_type == "2":
                todos = sorted((x for x in reader if x), key=lambda x: datetime.strptime(x[2], "%Y-%m-%d %H:%M:%S"))
                print("To-Dos Sorted by Date Submitted:")
                for row in todos:
                    print(f"To-Do: {row[0]}, Difficulty: {row[1]}, Date Submitted: {row[2]}, Status: {row[3]}")
            elif view_type == "3":
                print("All To-Dos:")
                for row in reader:
                    if row:
                        print(f"To-Do: {row[0]}, Difficulty: {row[1]}, Date Submitted: {row[2]}, Status: {row[3]}")
            elif view_type == "4":
                todos = [x for x in reader if x]
                for i, row in enumerate(todos):
                    print(f"{i + 1}. {row[0]}, Difficulty: {row[1]}, Date Submitted: {row[2]}, Status: {row[3]}")
                mark_index = int(input("Enter the number of the to-do to mark as done: ")) - 1
                if 0 <= mark_index < len(todos):
                    todos[mark_index][3] = "Done"
                    with open(LOG_FILE, "w", newline="") as log_file:
                        writer = csv.writer(log_file)
                        writer.writerows(todos)
                    print("To-do marked as done!")
                else:
                    print("Invalid selection.")

elif option == "3":
    if not os.path.exists(LOG_FILE):
        print("No to-dos logged yet.")
    else:
        with open(LOG_FILE, "r") as log_file:
            todos = [x for x in csv.reader(log_file) if x]
        for i, row in enumerate(todos):
            print(f"{i + 1}. {row[0]}, Difficulty: {row[1]}, Date Submitted: {row[2]}, Status: {row[3]}")
        remove_index = int(input("Enter the number of the to-do to remove: ")) - 1
        if 0 <= remove_index < len(todos):
            todos.pop(remove_index)
            with open(LOG_FILE, "w", newline="") as log_file:
                writer = csv.writer(log_file)
                writer.writerows(todos)
            print("To-do removed successfully!")
        else:
            print("Invalid selection.")