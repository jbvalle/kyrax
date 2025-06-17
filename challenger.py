#!/usr/bin/env python3
import subprocess
import json
import inquirer
import sys


def get_repo_labels(repo=None):
    try:
        cmd = ["gh", "label", "list","--limit", "1000", "--json", "name"]
        if repo:
            cmd += ["--repo", repo]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        labels = json.loads(result.stdout)
        return [label['name'] for label in labels]
    except subprocess.CalledProcessError as e:
        print(f"Error fetching labels: {e.stderr}")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return []


def choose_labels_menu(labels):
    if not labels:
        print("No labels to display.")
        return []

    questions = [
        inquirer.Checkbox(
            "selected_labels",
            message="? Select one or more labels",
            choices=labels
        )
    ]
    answers = inquirer.prompt(questions)
    return answers.get("selected_labels", []) if answers else []


def get_issues_by_labels(labels, repo=None):
    try:
        label_arg = ",".join(labels)
        cmd = ["gh", "issue", "list", "--state", "open", "--label", label_arg, "--json", "number,title,labels"]
        if repo:
            cmd += ["--repo", repo]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issues = json.loads(result.stdout)
        return issues
    except subprocess.CalledProcessError as e:
        print(f"Error fetching issues: {e.stderr}")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return []


def print_issues(issues):
    if not issues:
        print("\n⚠️  No issues found with the selected labels.")
        return

    print(f"\n✅ Found {len(issues)} open issue(s):\n")
    for issue in issues:
        labels = [l['name'] for l in issue['labels']]
        print(f"#{issue['number']}: {issue['title']}")
        print(f"   Labels: {', '.join(labels)}\n")


def main():
    repo = None
    if len(sys.argv) > 1:
        repo = sys.argv[1]  # e.g., owner/repo-name

    labels = get_repo_labels(repo)
    selected_labels = choose_labels_menu(labels)

    if not selected_labels:
        print("\n⚠️  No labels selected.")
        return

    issues = get_issues_by_labels(selected_labels, repo)
    print_issues(issues)


if __name__ == "__main__":
    main()

