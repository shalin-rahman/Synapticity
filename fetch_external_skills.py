#!/usr/bin/env python3
"""
Fetch skills from addyosmani/agent-skills GitHub repository
and integrate them into Synapticity's skills-external directory.
"""

import requests
import os
import base64


def fetch_github_directory(api_url: str):
    """Fetch directory listing from GitHub API."""
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_file_content(download_url: str):
    """Fetch raw file content from GitHub."""
    response = requests.get(download_url)
    response.raise_for_status()
    return response.text


def main():
    base_api = "https://api.github.com/repos/addyosmani/agent-skills/contents/skills"
    output_dir = "skills-external/addyosmani-agent-skills"

    print("[FETCH] Discovering skills from addyosmani/agent-skills...")

    try:
        items = fetch_github_directory(base_api)
    except Exception as e:
        print(f"[ERROR] Failed to fetch directory listing: {e}")
        return 1

    os.makedirs(output_dir, exist_ok=True)

    # Create a README for attribution
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# External Skills: addyosmani/agent-skills\n\n")
        f.write("Source: https://github.com/addyosmani/agent-skills\n\n")
        f.write("Fetched automatically by Synapticity framework.\n")

    downloaded = 0
    skipped = 0

    for item in items:
        name = item["name"]
        item_type = item["type"]

        if item_type == "dir":
            # It's a skill directory - fetch its contents
            skill_dir = os.path.join(output_dir, name)
            os.makedirs(skill_dir, exist_ok=True)

            try:
                skill_items = fetch_github_directory(item["url"])
            except Exception as e:
                print(f"  [SKIP] {name}: {e}")
                skipped += 1
                continue

            for skill_item in skill_items:
                if skill_item["type"] == "file":
                    file_name = skill_item["name"]
                    try:
                        content = fetch_file_content(skill_item["download_url"])
                        file_path = os.path.join(skill_dir, file_name)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"  [OK] {name}/{file_name}")
                    except Exception as e:
                        print(f"  [FAIL] {name}/{file_name}: {e}")
                        skipped += 1

            downloaded += 1

        elif item_type == "file" and name.endswith(".md"):
            # Standalone markdown file
            try:
                content = fetch_file_content(item["download_url"])
                # Create a directory for it
                skill_name = name.replace(".md", "")
                skill_dir = os.path.join(output_dir, skill_name)
                os.makedirs(skill_dir, exist_ok=True)

                file_path = os.path.join(skill_dir, "skill.md")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  [OK] {name} -> {skill_name}/skill.md")
                downloaded += 1
            except Exception as e:
                print(f"  [FAIL] {name}: {e}")
                skipped += 1

    print(f"\n[DONE] Downloaded {downloaded} skills, {skipped} skipped.")
    print(f"Output directory: {output_dir}/")
    return 0


if __name__ == "__main__":
    exit(main())
