from datetime import datetime
import json
import sys
import os
import requests

token = os.environ.get("GITHUB_TOKEN")

keywords = [
    # kts
    "id(\"net.weavemc.gradle\")",  # weave 1.0
    "id(\"com.github.weave-mc.weave-gradle\")",
    # groovy
    "id \"net.weavemc.gradle\"",  # weave 1.0
    "id \"com.github.weave-mc.weave-gradle\""
]


def search(content):
    url = f"https://api.github.com/search/code?q={content}"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    response = requests.get(url, headers=headers)
    return response.json()


def main():
    print("Welcome to Weave Index!")
    if token is None or not token.startswith("github_pat_"):
        print("Error: Please generate a GitHub API token first")
        print("https://github.com/settings/personal-access-tokens")
        sys.exit(1)
    print("Indexing...")
    mods = []
    repository_index = set()
    for keyword in keywords:
        print("Searching for: " + keyword)
        search_result = search(keyword)
        if "status" in search_result and search_result["status"] == "401":
            print(f"Error: {search_result['message']}")
            sys.exit(1)
        if search_result["incomplete_results"]:
            print("Error: Failed to search.")
            continue
        code_data = search_result["items"]
        for code in code_data:
            filename: str = code["name"]
            if filename.startswith("build.gradle"):
                repository_name = code["repository"]["full_name"]
                if repository_name in repository_index:
                    continue  # already added
                print(f"Found {repository_name}")
                mods.append({
                    "name": code["repository"]["name"],
                    "repository": repository_name,
                    "url": "https://github.com/" + repository_name,
                    "description": code["repository"]["description"]
                })
                repository_index.add(repository_name)
    print("Saving indexes")
    date = datetime.now().isoformat()
    index_by_repository = {
        "timestamp": date,
        "mods": mods
    }
    with open("index-by-repository.json", "w") as f:
        json.dump(index_by_repository, f, indent=2)
    # https://github.com/emirsassan/weave-index/blob/main/ModIndex.json
    developers_map = {}
    for mod in mods:
        developer = mod["repository"].split("/")[0]
        if developer not in developers_map:
            developers_map[developer] = []
        developers_map[developer].append(mod)
    index_by_developers = {
        "timestamp": date,
        "developers": [
            {"name": name, "projects": projects}
            for name, projects in developers_map.items()
        ]
    }
    with open("index-by-developers.json", "w") as f:
        json.dump(index_by_developers, f, indent=2)
    print(f"Finished! Found {len(mods)} mods")


if __name__ == '__main__':
    main()
