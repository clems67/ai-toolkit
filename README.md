## Docker
The application requires a data directory to store and access processed files. You must define this path in a `.env` file.<br>
Configure the path: Create and/or open `.env` and update `DATA_DIR` to point to your local data folder.

Run the program :<br>
`docker compose up`

## Windows
Pros : takes 5 times less RAM than Docker.<br>
Cons : Speech to text takes 10 times more time than Docker.

Authorization to run ps1 scripts :<br>
`Set-ExecutionPolicy -ExecutionPolicy Unrestricted`<br>
`Get-ExecutionPolicy` => should get `Unrestricted`

Setup environment :<br>
`.\bootstrap.ps1`

Run the program :<br>
`uv run python src/main.py`

## Linux
Authorization to run this bash script :<br>
`chmod +x bootstrap.sh`

Setup environment :<br>
`./bootstrap.sh`

Run the program :<br>
`uv run python src/main.py`