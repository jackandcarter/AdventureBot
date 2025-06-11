# AdventureBot

## Configuration

Create a `config.json` file in the project root or provide the settings via
environment variables. An example configuration is available in
`config.example.json`.

Environment variables will override values found in `config.json`:

- `DISCORD_TOKEN`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

If a variable is not provided, the loader falls back to the value in
`config.json`.
