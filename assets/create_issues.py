import yaml
import subprocess
import sys
import inquirer

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
            message="Select labels to apply to all issues",
            choices=available_labels,
        )
    ]
    answers = inquirer.prompt(questions)
    return answers["selected_labels"]

def prompt_for_stats():
    stats = ['STR', 'DEX', 'CONST', 'INT', 'WIS', 'CHAR']
    questions = [
        inquirer.Checkbox(
            'selected_stats',
            message='Select the stats to apply (value will be 1)',
            choices=stats
        )
    ]
    answers = inquirer.prompt(questions)
    return answers['selected_stats']

# === MAIN ===
if len(sys.argv) != 2:
    print("Usage: python create_issues.py <path_to_yaml_file>")
    sys.exit(1)

yaml_file_path = sys.argv[1]

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
            subprocess.run(command, check=True)
            print(f"✅ Created issue: {title} (Level {level_num})")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create issue: {title}")
            print(f"Error: {e}")

print("🎉 All issues processed!")
