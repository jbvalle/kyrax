#!/usr/bin/env python3
import inquirer
import yaml
import sys
import subprocess
import re
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

def close_issue(issue_number):
    try:
        # First get the issue title using JSON output
        view_result = subprocess.run(
            ["gh", "issue", "view", issue_number, "--json", "title"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON output to get title
        try:
            import json
            issue_data = json.loads(view_result.stdout)
            title = issue_data.get('title', '')
            if not title:
                print("Error: Could not retrieve issue title")
                return
        except Exception as e:
            print(f"Error parsing issue data: {str(e)}")
            return
        
        # Now close the issue
        close_result = subprocess.run(
            ["gh", "issue", "close", issue_number],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Print success message
        print(f"✓ Closed issue #{issue_number} ({title})")
        
        # Parse stats from title
        exp_match = re.search(r'exp\s+(\d+)', title, re.IGNORECASE)
        str_match = re.search(r'str\s+(\d+)', title, re.IGNORECASE)
        dex_match = re.search(r'dex\s+(\d+)', title, re.IGNORECASE)
        const_match = re.search(r'const\s+(\d+)', title, re.IGNORECASE)
        int_match = re.search(r'int\s+(\d+)', title, re.IGNORECASE)
        wis_match = re.search(r'wis\s+(\d+)', title, re.IGNORECASE)
        char_match = re.search(r'char\s+(\d+)', title, re.IGNORECASE)
        
        # Update character stats if any found
        if any([exp_match, str_match, dex_match, const_match, int_match, wis_match, char_match]):
            data = load_yaml_data()
            updated = False
            
            if exp_match:
                exp_value = int(exp_match.group(1))
                data['character']['current_xp'] += exp_value
                print(f"  + Added {exp_value} XP")
                updated = True
                
            if str_match:
                str_value = int(str_match.group(1))
                data['stats']['str']['value'] += str_value
                print(f"  + Added {str_value} STR")
                updated = True
                
            if dex_match:
                dex_value = int(dex_match.group(1))
                data['stats']['dex']['value'] += dex_value
                print(f"  + Added {dex_value} DEX")
                updated = True
                
            if const_match:
                const_value = int(const_match.group(1))
                data['stats']['const']['value'] += const_value
                print(f"  + Added {const_value} CONST")
                updated = True
                
            if int_match:
                int_value = int(int_match.group(1))
                data['stats']['int']['value'] += int_value
                print(f"  + Added {int_value} INT")
                updated = True
                
            if wis_match:
                wis_value = int(wis_match.group(1))
                data['stats']['wis']['value'] += wis_value
                print(f"  + Added {wis_value} WIS")
                updated = True
                
            if char_match:
                char_value = int(char_match.group(1))
                data['stats']['char']['value'] += char_value
                print(f"  + Added {char_value} CHAR")
                updated = True
                
            if updated:
                save_yaml_data(data)
                print("\nCharacter stats updated!")
                print(f"Current XP: {data['character']['current_xp']}")
                print("Updated stats:")
                for stat, info in data['stats'].items():
                    print(f"  - {stat.upper()}: {info['value']}")
            else:
                print("No stat updates found in title")
        else:
            print("No stat keywords found in title")
        
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {e.stderr}")
    except Exception as e:
        print(f"Error: {str(e)}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_habit()
        return
    if len(sys.argv) > 1 and sys.argv[1] == "habit":
        track_habit()
        return
    if len(sys.argv) > 2 and sys.argv[1] == "close":
        close_issue(sys.argv[2])
        return
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        print("\nky create   # Create new Habits")
        print("ky habit    # Track habits for today")
        print("ky close <issue-number>  # Close GitHub issue and claim rewards")
        return

if __name__ == "__main__":
    main()
