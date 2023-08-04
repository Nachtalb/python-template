import re
import subprocess
from pathlib import Path


def find_placeholders(text: str) -> list[str]:
    return re.findall(r"{{\s*(\w+)\s*}}", text)


def ask_user_for_values(placeholders: set[str]) -> dict[str, str]:
    values = {}
    for placeholder in placeholders:
        values[placeholder] = input(f"Please provide value for {placeholder}: ")
    return values


def replace_placeholders(text: str, values: dict[str, str]) -> str:
    for placeholder, value in values.items():
        text = text.replace(f"{{{{ {placeholder} }}}}", value)
    return text


def ask(text: str) -> bool:
    while True:
        answer = input(f"{text}? (Y/n): ") or "y"
        if answer.lower()[0] == "y":
            return True
        elif answer.lower()[0] == "n":
            return False


def git_filter(path: Path) -> bool:
    return ".git" not in path.parts


def main() -> None:
    root_dir = Path(".")  # root directory to search
    all_placeholders = set()

    # Find all placeholders in file content
    for file_path in filter(git_filter, root_dir.rglob("*")):
        if file_path.is_file():
            try:
                file_content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                print(f"Could not read file {file_path}, got a UnicodeDecodeError")
                continue
            all_placeholders.update(find_placeholders(file_content))

    # Get values from the user for all unique placeholders
    values = ask_user_for_values(all_placeholders)

    # Replace placeholders in files
    for file_path in filter(git_filter, root_dir.rglob("*")):
        if file_path.is_file():
            try:
                file_content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            new_content = replace_placeholders(file_content, values)
            if new_content != file_content:
                print(f"Replacing variables in '{file_path}'")
                file_path.write_text(new_content)

            new_file_name = replace_placeholders(file_path.name, values)
            if new_file_name != file_path.name:
                print(f"Renaming file to '{new_file_name}'")
                file_path.rename(file_path.with_name(new_file_name))

    # Rename folders
    for folder_path in list(filter(git_filter, root_dir.rglob("*")))[::-1]:  # Reversed to rename subdirectories first
        if not folder_path.is_dir():
            continue
        new_folder_name = replace_placeholders(folder_path.name, values)
        if new_folder_name != folder_path.name:
            print(f"Rename folder to '{new_folder_name}'")
            folder_path.rename(folder_path.with_name(new_folder_name))

    # Ask to delete script
    if ask("Do you want to delete this script"):
        script_path = Path(__file__)
        script_path.unlink()
        print("Script has been deleted.")

    # Ask to run poetry install
    if ask("Do you want to run `poetry install`"):
        subprocess.run(["poetry", "install"])
        print("Poetry install finished.")

        # Ask to install pre-commit hooks
        if ask("Do you want to install pre-commit hooks"):
            subprocess.run(["poetry", "run", "pre-commit", "install"])
            print("Poetry install finished.")

        # Ask to update dependencies
        if ask("Do you want me to update all dependencies"):
            subprocess.run(["poetry", "update"])
            subprocess.run(["poetry", "run", "pre-commit", "autoupdate"])
            print("Poetry install finished.")

    # Ask to commit changes
    if ask("Do you want to commit the changes"):
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "Set up project from template by filling in placeholders"])
        print("Changes have been committed.")


if __name__ == "__main__":
    main()
