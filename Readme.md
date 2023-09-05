# Overview
This repository is designed to calculate the productivity of each user based on the number of commits made in the last N days. It is only assumption for the practice and should not be used in a real world.

## Repository Structure
- `.env`: Configuration file for MongoDB.
- `docker-compose.yaml`: Docker Compose file to run MongoDB and MongoExpress.
- `./mongodb_data`: This folder is created when you run docker-compose and is used to store MongoDB data.
- `requirements.txt`: Contains all the dependencies required for Python.

## Installation
To get started, follow these steps:
- Set up a virtual environment for Python 3.11.0 using `pyenv-virtualenv` or the built-in `venv` module.
- Upgrade pip to the newest version `python -m pip install --upgrade pip`
- Install requirements `pip install -r requirements.txt`
- Run command `docker-compose up -d`
- Run command `python productivity.py --help` to view the usage instructions.

## Usage and information
- To download commit data for a repository, simply use the `productivity.py` script with the `-r` flag followed by the repository URL copied from your browser. For example: https://github.com/torvalds/linux.
- Each time you make a request, all data will be written to MongoDB, and you will see an output message like:
   `Total added commits to MongoDB "torvalds" database and "linux" collection is 300`
    Read the NOTE: section for more information
- There is a configuration, preventing duplicating data in mongo db. I create index for commit ID as unique value to do so.
- The data stored in MongoDB follows this structure: the database name corresponds to the username, and the collection name is the GitHub repository name. 
- You can manually verify the data in MongoDB by accessing it via `localhost:8081` in your browser.
- Use `--dry-run` flag to prevent requests to GitHub. It builds result from MongoDB. Data should be presented in MongoDB.
- To load data and build result use command similar to this one `python productivity.py -r https://github.com/torvalds/linux`
- To show commits only for the last N days use flag `-d NUMBER_OF_DAYS`. Example: `python productivity.py -r https://github.com/torvalds/linux --days-to-filter 30`. Default value is 10.

## Roadmap
- Add exceptions for requests
- Add script argument -all which build result for all repos
- Build graphs with matplotlib lib
   