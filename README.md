# CoreService

CoreService is a Python application that acts as a core service, utilizing RabbitMQ for messaging and providing various endpoints for interaction.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Folder Structure](#folder-structure)
- [Contributing](#contributing)
- [License](#license)

## Requirements

- Python 3.12.7
- RabbitMQ server
- Virtualenv

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/coreService.git
    cd coreService
    ```

2. **Create a virtual environment:**

    ```sh
    python -m venv venv
    ```

3. **Activate the virtual environment:**

    - On Windows:

        ```sh
        venv\Scripts\activate
        ```

    - On macOS/Linux:

        ```sh
        source venv/bin/activate
        ```

4. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

## Configuration

1. **Environment Variables:**

    Create a `.env` file in the project root directory with the following content:

    ```env
    RABBITMQ_URL=amqp://guest:guest@localhost:5672/
    SERVICE_NAME=coreService
    ```

    Adjust the values as needed.

2. **Settings Configuration:**

    The application settings are managed using `pydantic-settings`. Here is an example configuration class:

    ```python
    import os
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        service_name: str = "coreService"

        model_config = SettingsConfigDict(env_file=".env")
    ```

## Running the Application

To run the application, execute the following command:

```sh
python main.py
```

Ensure RabbitMQ server is running and accessible via the URL specified in your `.env` file.

## Running Tests

To run the test suite, use the following command:

```sh
pytest
```

The tests are located in the `tests` directory and are written using the `pytest` framework.

## Folder Structure

- `app/`: Contains the main application code.
    - `main.py`: Entry point of the application.
    - `config.py`: Application configuration.
- `tests/`: Contains unit and integration tests.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature-branch`)
6. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.