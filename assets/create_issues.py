import yaml
import subprocess

# Load the YAML file
with open('embeddedIoT_prj.yaml', 'r') as file:
    data = yaml.safe_load(file)

# Process each level
for level in data['levels']:
    level_num = level['level']
    theme = level['theme']
    
    for project in level['projects']:
        name = project['name']
        requirements = project['requirements']
        
        # Format title with suffix
        title = f"{name} dex 1, int 1"
        
        # Format the body
        body = f"## {name}\n\n**Level {level_num} - {theme}**\n\n### Requirements:\n"
        body += "\n".join([f"- {req}" for req in requirements])
        
        # Format labels
        labels = [
            "area: embedded_systems",
            "area: embedded_IoT_challenges",
            f"level {level_num}"
        ]
        
        # Build the command
        command = [
            "gh", "issue", "create",
            "--title", title,
            "--body", body,
        ]
        
        # Add labels
        for label in labels:
            command.extend(["--label", label])
        
        # Execute the command
        try:
            subprocess.run(command, check=True)
            print(f"Created issue: {title} (Level {level_num})")
        except subprocess.CalledProcessError as e:
            print(f"Failed to create issue: {title}")
            print(f"Error: {e}")

print("All issues processed!")
