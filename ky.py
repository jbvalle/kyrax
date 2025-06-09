#!/usr/bin/env python3
#test

import inquirer
import yaml
import sys
from datetime import datetime, timedelta  # Add this at the top of your imports



def load_yaml_data():
    with open('kyrax.yaml', 'r') as file:
        return yaml.safe_load(file)

def save_yaml_data(data):
    with open('kyrax.yaml', 'w') as file:
        yaml.dump(data, file, sort_keys=False)

def create_habit():
    print("\nCreating habit:\n")
    
    questions = [
        inquirer.Text('name', message="? Title"),
        inquirer.Text('value', message="? EXP"),
        inquirer.List('action',
                     message="? What's next?",
                     choices=['Submit', 'Cancel'])
    ]
    
    answers = inquirer.prompt(questions)

    if answers is None or not answers['action']:
        print("\nError: Habit Creation::create_habit()")
    else:
        if answers['action'] == 'Submit':
            data = load_yaml_data()
            new_id = max(habit['id'] for habit in data['habit_data']) + 1 if data['habit_data'] else 1
            new_habit = {
                'id': new_id,
                'name': answers['name'],
                'value': int(answers['value']),
                'compounded_value': int(answers['value']),  # Same as value initially
                'last_executed': datetime.now().strftime('%Y-%m-%d')  # Current date in YYYY-MM-DD format
            }
            data['habit_data'].append(new_habit)
            save_yaml_data(data)
            print(f"\nHabit '{answers['name']}' added successfully!")
        else:
            print("\nOperation canceled.")

def track_habit():
    # Load current data
    data = load_yaml_data()
    habit_data = data['habit_data']
    today = datetime.now().date()

    questions = [
        inquirer.Checkbox(
            "habits",
            message="? What would you like to choose?",
            choices=[
                (f"{habit['id']}. {habit['name']} (EXP {habit['value']})", habit) for habit in habit_data
            ],
        ),
    ]

    answers = inquirer.prompt(questions)

    if answers is None or not answers['habits']:
        print("\nNo habits selected")
    else:
        total_xp = 0
        print("\nSelected habits:")
        
        for habit in answers['habits']:
            # Convert string date to datetime object
            last_executed = datetime.strptime(habit['last_executed'], '%Y-%m-%d').date()
            days_since = (today - last_executed).days
            
            if days_since == 1:
                # Executed yesterday - apply compounding
                compounded_value = round(habit['compounded_value'] * 1.025)
                xp_gain = compounded_value
                habit['compounded_value'] = compounded_value
                print(f"{habit['id']}. {habit['name']} (Compounded EXP: {xp_gain}!)")
            else:
                # Reset to base value if >1 day or same day
                xp_gain = habit['value']
                habit['compounded_value'] = habit['value']
                if days_since == 0:
                    print(f"{habit['id']}. {habit['name']} (EXP {xp_gain}) - Already tracked today")
                else:
                    print(f"{habit['id']}. {habit['name']} (EXP {xp_gain}) - Reset streak")
            
            # Update last executed date
            habit['last_executed'] = today.strftime('%Y-%m-%d')
            total_xp += xp_gain
        
        # Update current_xp
        data['character']['current_xp'] += total_xp
        save_yaml_data(data)
        
        print(f"\nAdded {total_xp} XP to your character!")
        print(f"Total XP: {data['character']['current_xp']}/{data['character']['xp_to_next_level']}")
        
        # Check for level up
        if data['character']['current_xp'] >= data['character']['xp_to_next_level']:
            print("\nLEVEL UP AVAILABLE!")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_habit()
        return
    if len(sys.argv) > 1 and sys.argv[1] == "habit":
        track_habit()
        return
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        print("\nky create #Create new Habits")
        print("\nky habit  #Track habits for today")
        return   

if __name__ == "__main__":
    main()
