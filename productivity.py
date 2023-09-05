import argparse
import os
import matplotlib.pyplot
import pymongo
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv


def get_arguments():
    """
    Parse command-line arguments to retrieve them as variables.

    Returns:
        github_username (str): The username or organization name of the GitHub repository owner.
        github_reponame (str): The name of the GitHub repository.
        dry_run (bool): A boolean indicating whether a dry run should be performed.
                        True if specified, False otherwise.
    """
    parser = argparse.ArgumentParser(description="Calculate productivity for repository")
    parser.add_argument("--repository", "-r", required=True, help="GitHub repository URL (e.g., https://github.com/torvalds/linux)")
    parser.add_argument("--dry-run", required=False, action="store_true", help="[Optional] Do not make request to github, use only data from MongoDB")
    parser.add_argument("--days-to-filter", "-d", type=int, default=30, required=False, help="[Optional] Specify the number of days to filter commits (default: 30)")

    args = parser.parse_args()

    repository_url = args.repository
    github_username = repository_url.split("/")[-2]
    github_reponame = repository_url.split("/")[-1]
    days_to_filter = args.days_to_filter
    dry_run = args.dry_run

    return github_username, github_reponame, dry_run, days_to_filter

def load_env_file(env_file_path=".env"):
    """
    Load environment variables from a specified .env file.

    Args:
        env_file_path (str, optional): The path to the .env file. Defaults to ".env" in the current directory.

    Returns:
        mongodb_username (str): The username for MongoDB authentication.
        mongodb_password (str): The password for MongoDB authentication.
        mongodb_host (str): The hostname or IP address of the MongoDB server.
        mongodb_port (str): The port number for the MongoDB server.
    """
    # Load variables from the .env file
    load_dotenv(env_file_path)

    # Set variables from the .env file
    mongodb_username = os.getenv("mongodb_username")
    mongodb_password = os.getenv("mongodb_password")
    mongodb_host = os.getenv("mongodb_host")
    mongodb_port = os.getenv("mongodb_port")

    return mongodb_username, mongodb_password, mongodb_host, mongodb_port

def mongodb_open():
    mongo_client = pymongo.MongoClient(f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_host}:{mongodb_port}/")
    mongo_db = mongo_client[github_username]
    mongo_collection = mongo_db[github_reponame]
    mongo_collection.create_index([("sha", pymongo.ASCENDING)], unique=True)

    return mongo_client, mongo_db, mongo_collection

def mongodb_close(mongo_client):
    if mongo_client:
        mongo_client.close()

def load_github_commits_data(github_username, github_reponame):
    # Default headers for github. Authorization token can be added here for private repositories
    headers = {
        "X-GitHub-Api-Version": "2022-11-28",  # API version
    }

    # Open connection to MongoDB
    mongo_client, mongo_db, mongo_collection = mongodb_open()

    page = 1
    successful_insertions = 0
    
    # NOTE: If you want to fetch all commits just put: "while True:". Be careful, some repositories have 1M+ commits
    #       so github can decline such big requests.
    #       For our model I fetch not more than 300 commits.
    while page <= 3:
        commits_url = f"https://api.github.com/repos/{github_username}/{github_reponame}/commits?page={page}&per_page=100"
        response = requests.get(commits_url, headers=headers)
        
        if response.status_code == 200:
            commits_data = response.json()
            
            if not commits_data:
                break
            
            for commit in commits_data:
                try:
                    # Insert a unique commit to MongoDB
                    mongo_collection.insert_one(commit)
                    successful_insertions += 1

                except pymongo.errors.DuplicateKeyError:
                    pass  # Ignore the error silently

            # Move to the next page
            page += 1
        else:
            print("Failed to fetch commit data.")
            break
    
    print(f"Total added commits to MongoDB \"{github_username}\" database and \"{github_reponame}\" collection is {successful_insertions}")

    mongodb_close(mongo_client)


def build_result(days_to_filter):
    """
    Fetches and analyzes commit data from a MongoDB collection, allowing users to specify a time range for filtering commits.

    Args:
        days_to_filter (int): The number of days to consider when filtering commits.

    The function connects to a MongoDB collection containing commit data and calculates commit statistics within a specified time frame.

    Example usage:
    To analyze commits from the last 5 days:
    build_result(days_to_filter=5)
    """
    mongo_client, mongo_db, mongo_collection = mongodb_open()

    # Calculate the start date (e.g., one year ago from the current date)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(days_to_filter))

    query = {
        "commit.author.date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
    }

    commits_data = list(mongo_collection.find(query))

    ##### My first solution prints result to terminal #####
    commit_count_per_user = {}
    for commit in commits_data:
        commit_author = commit["commit"]["author"]["name"]
        if commit_author in commit_count_per_user:
            commit_count_per_user[commit_author] += 1
        else:
            commit_count_per_user[commit_author] = 1

    # Sort the results by commit count in descending order
    sorted_results = dict(sorted(commit_count_per_user.items(), key=lambda x: x[1], reverse=True))

    print("Commit counts per user:")
    for user in sorted_results:
        print(f"{user}: {sorted_results[user]} commits")
    ##############################

    #### UPDATED solution #####
    # Create a chart using matplotlib
    matplotlib.pyplot.figure(figsize=(10, 6))
    matplotlib.pyplot.bar(sorted_results.keys(), sorted_results.values(), color='green')
    matplotlib.pyplot.xlabel('User')
    matplotlib.pyplot.ylabel('Commit Count')
    matplotlib.pyplot.title(f'Commit Counts per User (Last {days_to_filter} days)')
    matplotlib.pyplot.xticks(rotation=90, fontsize=9)
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.show()
    ###########################

    mongodb_close(mongo_client)


if __name__ == "__main__":
    # Set up global variables from script arguments and .env
    github_username, github_reponame, dry_run, days_to_filter = get_arguments()
    mongodb_username, mongodb_password, mongodb_host, mongodb_port = load_env_file()
    
    if not dry_run:
        load_github_commits_data(github_username, github_reponame)

    build_result(days_to_filter)