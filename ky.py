import inquirer

def main():
    # Define habits with ID, name, and value
    habit_data = [
        {"id": 1, "name": "Habit1", "value": 100},
        {"id": 2, "name": "Habit2", "value": 200},
        {"id": 3, "name": "Habit3", "value": 300},
    ]

    # Use (display string, internal dict) as choices
    questions = [
        inquirer.Checkbox(
            "habits",
            message="? What would you like to choose?",
            choices=[
                (f"{habit['id']}. {habit['name']} (${habit['value']})", habit) for habit in habit_data
            ],
        ),
    ]

    answers = inquirer.prompt(questions)

    if answers is None or not answers['habits']:
        print("\nNo habits selected")
    else:
        print("\nSelected habits:")
        for habit in answers['habits']:
            print(f"- ID: {habit['id']}, Name: {habit['name']}, Value: {habit['value']}")

if __name__ == "__main__":
    main()

