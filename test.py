#!/usr/bin/env python3
import inquirer
import yaml
import sys
import subprocess
import re
import math
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
    elif answers['action'] == 'Submit':
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
        return

    total_xp = 0
    print("\nSelected habits:")
    for habit in answers['habits']:
        last_executed = datetime.strptime(habit['last_executed'], '%Y-%m-%d').date()
        days_since = (today - last_executed).days
        if days_since == 1:
            compounded_value = round(habit['compounded_value'] * 1.025)
            xp_gain = compounded_value
            habit['compounded_value'] = compounded_value
            print(f"{habit['id']}. {habit['name']} (Compounded EXP: {xp_gain}!)")
        else:
            xp_gain = habit['value']
            habit['compounded_value'] = habit['value']
            if days_since == 0:
                print(f"{habit['id']}. {habit['name']} (EXP {xp_gain}) - Already tracked today")
            else:
                print(f"{habit['id']}. {habit['name']} (EXP {xp_gain}) - Reset streak")
        habit['last_executed'] = today.strftime('%Y-%m-%d')
        total_xp += xp_gain
    data['character']['current_xp'] += total_xp
    save_yaml_data(data)
    print(f"\nAdded {total_xp} XP to your character!")
    print(f"Total XP: {data['character']['current_xp']}/{data['character']['xp_to_next_level']}")
    if data['character']['current_xp'] >= data['character']['xp_to_next_level']:
        print("\nLEVEL UP AVAILABLE!")


def close_issue(issue_number):
    try:
        view_result = subprocess.run(
            ["gh", "issue", "view", issue_number, "--json", "title"],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        issue_data = json.loads(view_result.stdout)
        title = issue_data.get('title', '')
        if not title:
            print("Error: Could not retrieve issue title")
            return
        close_result = subprocess.run(
            ["gh", "issue", "close", issue_number],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Closed issue #{issue_number} ({title})")
        patterns = {
            'exp': re.IGNORECASE, 'str': re.IGNORECASE, 'dex': re.IGNORECASE,
            'const': re.IGNORECASE, 'int': re.IGNORECASE, 'wis': re.IGNORECASE,
            'char': re.IGNORECASE
        }
        matches = {key: re.search(fr"{key}\s+(\d+)", title, flags)
                   for key, flags in patterns.items()}
        if any(matches.values()):
            data = load_yaml_data()
            updated = False
            for stat, match in matches.items():
                if match:
                    val = int(match.group(1))
                    if stat == 'exp':
                        data['character']['current_xp'] += val
                        print(f"  + Added {val} XP")
                    else:
                        data['stats'][stat]['value'] += val
                        print(f"  + Added {val} {stat.upper()}")
                    updated = True
            if updated:
                save_yaml_data(data)
                print("\nCharacter stats updated!")
                print(f"Current XP: {data['character']['current_xp']}")
                print("Updated stats:")
                for stat, info in data['stats'].items():
                    print(f"  - {stat.upper()}: {info['value']}")
        else:
            print("No stat keywords found in title")
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {e.stderr}")
    except Exception as e:
        print(f"Error: {str(e)}")


def check_level():
    data = load_yaml_data()
    current_xp = data['character']['current_xp']
    current_level = data['character'].get('level', 1)
    new_level = int(math.sqrt(current_xp / 110))
    if new_level > current_level:
        data['character']['level'] = new_level
        save_yaml_data(data)
        print(f"\n🎉 Congratulations! You've reached Level {new_level}! 🎉")


def print_help():
    print("\nky create   # Create new Habits")
    print("ky habit    # Track habits for today")
    print("ky close <issue-number>  # Close GitHub issue and claim rewards")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "create":
            create_habit()
        elif cmd == "habit":
            track_habit()
        elif cmd == "close" and len(sys.argv) > 2:
            close_issue(sys.argv[2])
        elif cmd == "help":
            print_help()
        else:
            print_help()
    else:
        print_help()
    # After any command, check for level up
    check_level()


if __name__ == "__main__":
    main()

