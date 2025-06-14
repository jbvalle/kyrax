import yaml
import subprocess
import sys
import inquirer
import tempfile
import os

def get_repo_labels():
    try:
        result = subprocess.run(
            ["gh", "label", "list", "--limit", "1000"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split('\n')
        labels = [line.split('\t')[0] for line in lines if line]
        return labels
    except subprocess.CalledProcessError as e:
        print("Failed to fetch labels from GitHub.")
        print(f"Error: {e}")
        sys.exit(1)

def create_label_if_not_exists(label_name):
    existing_labels = get_repo_labels()
    if label_name not in existing_labels:
        try:
            subprocess.run(
                ["gh", "label", "create", label_name],
                check=True
            )
            print(f"Created new label: {label_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to create label: {label_name}")
            print(f"Error: {e}")
            return False
    return True

def prompt_for_labels(available_labels):
    questions = [
        inquirer.Checkbox(
            "selected_labels",
            message="Select labels to apply to the issue",
            choices=available_labels,
        )
    ]
    answers = inquirer.prompt(questions)
    return answers["selected_labels"]

def prompt_for_stats():
    stats = {
        'STR': None,
        'DEX': None,
        'CONST': None,
        'INT': None,
        'WIS': None,
        'CHAR': None
    }
    
    for stat in stats.keys():
        questions = [
            inquirer.Text(
                stat.lower(),
                message=f"Enter value for {stat} (leave empty for 0)",
                default="0"
            )
        ]
        answers = inquirer.prompt(questions)
        stats[stat] = answers[stat.lower()]
    
    # Filter out stats with 0 value
    return {k: v for k, v in stats.items() if v != "0"}

def update_yaml_with_new_project(yaml_file_path, level_num, project_data):
    try:
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file) or {'levels': []}
            
        # Find or create the level
        level_found = False
        for level in data['levels']:
            if level['level'] == level_num:
                level['projects'].append(project_data)
                level_found = True
                break
                
        if not level_found:
            data['levels'].append({
                'level': level_num,
                'theme': f"Custom Level {level_num}",
                'projects': [project_data]
            })
                
        # Write the updated data back to the YAML file
        with open(yaml_file_path, 'w') as file:
            yaml.dump(data, file, sort_keys=False)
            
    except Exception as e:
        print(f"Error updating YAML file with new project: {e}")
        sys.exit(1)

def extract_issue_number(output):
    try:
        return output.strip().split('/')[-1]
    except:
        return None

def get_body_input():
    questions = [
        inquirer.List(
            'input_method',
            message="How would you like to enter the issue body?",
            choices=['Single line input', 'Open nvim editor'],
        )
    ]
    answers = inquirer.prompt(questions)
    
    if answers['input_method'] == 'Single line input':
        questions = [
            inquirer.Text('body', message="Enter the issue body (requirements)")
        ]
        answers = inquirer.prompt(questions)
        return answers['body']
    else:
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Open nvim editor
            subprocess.run(['nvim', tmp_path], check=True)
            
            # Read the content
            with open(tmp_path, 'r') as f:
                content = f.read()
            
            os.unlink(tmp_path)
            return content
        except Exception as e:
            print(f"Error using editor: {e}")
            os.unlink(tmp_path)
            sys.exit(1)

def prompt_for_level():
    questions = [
        inquirer.Text(
            'level',
            message="Enter the level number for this project",
            validate=lambda _, x: x.isdigit()
        )
    ]
    answers = inquirer.prompt(questions)
    return int(answers['level'])

def prompt_for_skill():
    questions = [
        inquirer.Text(
            'skill',
            message="Enter the skill for this project (optional)",
        )
    ]
    answers = inquirer.prompt(questions)
    return answers['skill'] or None

def create_custom_issue(yaml_file_path):
    print("Creating a custom GitHub issue...")
    
    # Prompt for title
    questions = [
        inquirer.Text('title', message="Enter the issue title (project name)")
    ]
    answers = inquirer.prompt(questions)
    title = answers['title']
    
    # Get body content
    body = get_body_input()
    
    # Prompt for level
    level_num = prompt_for_level()
    
    # Prompt for stats
    stats = prompt_for_stats()
    
    # Add stats to title if any
    if stats:
        stat_str = ", ".join(f"{k.lower()} {v}" for k, v in stats.items())
        title = f"{title}. {stat_str}"
    
    # Get available labels and prompt for selection
    available_labels = get_repo_labels()
    selected_labels = prompt_for_labels(available_labels)
    
    # Add level label
    selected_labels.append(f"level {level_num}")
    
    # Prompt for skill and create skill label if provided
    skill = prompt_for_skill()
    if skill:
        skill_label = f"skill: {skill}"
        if create_label_if_not_exists(skill_label):
            selected_labels.append(skill_label)
    
    # Create the issue
    command = ["gh", "issue", "create", "--title", title, "--body", body]
    for label in selected_labels:
        command.extend(["--label", label])
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        issue_number = extract_issue_number(result.stdout)
        
        if issue_number:
            # Prepare project data for YAML
            project_data = {
                'name': title.split('.')[0],  # Remove stats from name
                'state': 'locked',
                'requirements': body.split('\n'),  # Split body into lines
                'gh_issue': issue_number
            }
            
            if skill:
                project_data['skill'] = skill
            
            # Update YAML file
            update_yaml_with_new_project(yaml_file_path, level_num, project_data)
            print(f"✅ Created issue #{issue_number}: {title} (Level {level_num})")
        else:
            print(f"⚠️  Created issue but couldn't determine issue number: {title}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create issue: {title}")
        print(f"Error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 create_issue.py <yaml_file> - Process all projects in YAML")
        print("  python3 create_issue.py custom <yaml_file> - Create custom issue")
        sys.exit(1)
    
    if sys.argv[1].lower() == 'custom':
        if len(sys.argv) != 3:
            print("Usage: python3 create_issue.py custom <yaml_file>")
            sys.exit(1)
        yaml_file_path = sys.argv[2]
        create_custom_issue(yaml_file_path)
    else:
        yaml_file_path = sys.argv[1]
        process_yaml_file(yaml_file_path)

def process_yaml_file(yaml_file_path):
    # Load YAML
    try:
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File '{yaml_file_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)

    # Fetch and choose labels
    available_labels = get_repo_labels()
    selected_labels = prompt_for_labels(available_labels)

    # Prompt for stats
    selected_stats = prompt_for_stats()
    stat_suffix = ", ".join(f"{stat.lower()} 1" for stat in selected_stats)

    # Process each level and project
    for level in data['levels']:
        level_num = level['level']
        theme = level['theme']

        for project in level['projects']:
            # Skip if this project already has an issue number
            if 'gh_issue' in project:
                print(f"ℹ️  Skipping {project['name']} - already has issue #{project['gh_issue']}")
                continue
                
            name = project['name']
            requirements = project['requirements']

            title = f"{name}. {stat_suffix}" if stat_suffix else name
            body = f"## {name}\n\n**Level {level_num} - {theme}**\n\n### Requirements:\n"
            body += "\n".join([f"- {req}" for req in requirements])

            command = ["gh", "issue", "create", "--title", title, "--body", body]

            # Start with the selected labels and level label
            labels_to_apply = selected_labels.copy() + [f"level {level_num}"]
            
            # Check for skill field and add it as a label if present
            if 'skill' in project:
                skill_label = f"skill: {project['skill']}"
                if create_label_if_not_exists(skill_label):
                    labels_to_apply.append(skill_label)

            # Add all labels to the command
            for label in labels_to_apply:
                command.extend(["--label", label])

            try:
                # Capture output to get issue number
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                issue_number = extract_issue_number(result.stdout)
                
                if issue_number:
                    # Update the YAML file with the issue number
                    update_yaml_with_issue_number(yaml_file_path, level_num, name, issue_number)
                    print(f"✅ Created issue #{issue_number}: {title} (Level {level_num})")
                else:
                    print(f"⚠️  Created issue but couldn't determine issue number: {title}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to create issue: {title}")
                print(f"Error: {e}")

    print("🎉 All issues processed!")

def update_yaml_with_issue_number(yaml_file_path, level_num, project_name, issue_number):
    try:
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)
            
        # Find the project and update/add gh_issue field
        for level in data['levels']:
            if level['level'] == level_num:
                for project in level['projects']:
                    if project['name'] == project_name:
                        project['gh_issue'] = issue_number
                        break
                break
                
        # Write the updated data back to the YAML file
        with open(yaml_file_path, 'w') as file:
            yaml.dump(data, file, sort_keys=False)
            
    except Exception as e:
        print(f"Error updating YAML file with issue number: {e}")

if __name__ == "__main__":
    main()
