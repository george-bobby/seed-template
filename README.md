# Application Seeding Template

This is a template repository for seeding data into applications. It provides a structured approach to generating and seeding test data using AI-powered generation and automated seeding scripts.

## Overview

This template includes:
- **CLI commands** for managing containers and seeding data
- **Data generation** using AI (Anthropic Claude)
- **Seeding functions** for populating your application
- **Utility functions** for API interactions, database operations, and data manipulation
- **Docker configuration** for running your application locally

## Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Anthropic API key (for AI-powered data generation)

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your configuration:
   ```env
   ANTHROPIC_API_KEY=your_api_key_here
   APP_API_URL=http://localhost:80
   APP_ADMIN_EMAIL=admin
   APP_ADMIN_PASSWORD=admin
   DATABASE_URL=mysql://dev:dev@localhost:3306/app_db
   ```

## Directory Structure

```
.
├── config/              # Configuration files
│   ├── constants.py     # Application constants and enums
│   └── settings.py      # Settings loaded from environment
├── core/                # Seeding functions
│   └── example_entity.py  # Example seeding function
├── data/                # Generated data files (JSON)
│   └── example_data.json  # Example data file
├── docker/              # Docker configuration
│   ├── docker-compose.yml
│   └── Dockerfile.php   # TODO: Replace with your backend Dockerfile
├── generate/            # Data generation scripts
│   └── example_generate.py  # Example generation function
├── utils/               # Utility functions
│   ├── api_utils.py    # API interaction helpers
│   ├── data_utils.py   # Data manipulation utilities
│   ├── database.py     # Database connection management
│   └── helpers.py      # General helper functions
└── app_cli.py          # Main CLI entry point
```

## Usage

### Starting the Application

```bash
python app_cli.py up
```

Start containers in detached mode:
```bash
python app_cli.py up --detach
```

### Stopping the Application

```bash
python app_cli.py down
```

This will stop containers and remove volumes.

### Generating Data

Generate seed data files:
```bash
python app_cli.py generate
```

### Seeding Data

Seed generated data into the application:
```bash
python app_cli.py seed
```

## Customization Guide

### 1. Update Configuration

Edit `config/settings.py` to match your application:
- Replace `APP_*` variables with your application's configuration
- Update `DATABASE_URL` to match your database connection string
- Adjust `DATA_THEME_SUBJECT` to describe your data domain

### 2. Define Constants

Edit `config/constants.py`:
- Add your application's API endpoints to `AppEndpoint` enum
- Define your data item types in `DataItemType` enum
- Set default counts and batch sizes for your entities

### 3. Create Seeding Functions

Use `core/example_entity.py` as a template:
- Copy and rename for each entity type you need to seed
- Update the form data building logic
- Adjust the endpoint paths
- Customize the database table and column names

### 4. Create Generation Functions

Use `generate/example_generate.py` as a template:
- Copy and rename for each entity type
- Customize the prompt to match your data requirements
- Adjust batch sizes and generation logic

### 5. Update Docker Configuration

Edit `docker/docker-compose.yml`:
- Replace service names with your application's services
- Update image names and Dockerfile paths
- Adjust ports and volumes as needed
- Set appropriate environment variables

### 6. Update CLI Commands

Edit `app_cli.py`:
- Import your seeding functions
- Import your generation functions
- Add them to the `seed()` and `generate()` commands

## Example Workflow

1. **Start the application:**
   ```bash
   python app_cli.py up
   ```

2. **Wait for the application to be ready** (check logs or wait for health checks)

3. **Generate data:**
   ```bash
   python app_cli.py generate
   ```
   This creates JSON files in the `data/` directory.

4. **Seed the data:**
   ```bash
   python app_cli.py seed
   ```
   This reads the JSON files and seeds them into your application.

5. **Stop when done:**
   ```bash
   python app_cli.py down
   ```

## Configuration Reference

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key for AI generation
- `DEFAULT_MODEL`: Claude model to use (default: `claude-3-5-haiku-20241022`)
- `APP_API_URL`: Base URL of your application API
- `APP_ADMIN_EMAIL`: Admin email for authentication
- `APP_ADMIN_PASSWORD`: Admin password for authentication
- `APP_SITE_NAME`: Site/tenant name (if multi-tenant)
- `DATABASE_URL`: Database connection string
- `DATA_THEME_SUBJECT`: Theme for generated data (e.g., "a technology consulting company")
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Best Practices

1. **Start Small**: Begin with one entity type, get it working, then add more
2. **Use Examples**: The example files show the pattern - customize them for your needs
3. **Test Incrementally**: Test generation and seeding separately
4. **Version Control**: Keep generated data files out of version control (add `data/*.json` to `.gitignore`)
5. **Documentation**: Update this README with your application-specific setup steps

## Troubleshooting

### Containers won't start
- Check Docker is running
- Verify ports aren't already in use
- Review docker-compose.yml for configuration errors

### Generation fails
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check API rate limits
- Review generation prompts for clarity

### Seeding fails
- Verify application is running and accessible
- Check database connection string
- Review API endpoint paths in your seeding functions
- Check authentication credentials

## Next Steps

1. Customize the configuration files for your application
2. Create seeding functions for your entity types
3. Create generation functions for your data needs
4. Update Docker configuration for your stack
5. Test the workflow end-to-end
6. Document any application-specific setup steps

## Support

For issues or questions, please refer to the example files in `core/` and `generate/` directories, which demonstrate the patterns used throughout this template.
