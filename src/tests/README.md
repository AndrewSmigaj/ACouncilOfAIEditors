# AI Council Guide Creation Website - Tests

This directory contains tests for the AI Council Guide Creation Website.

## Directory Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for multiple components working together

## Running Tests

### MongoDB Tests

To run the MongoDB connectivity and schema tests:

```bash
# From the project root directory
python -m pytest src/tests/unit/test_mongodb.py -v
```

### Running All Tests

To run all tests:

```bash
# From the project root directory
python -m pytest
```

## Test Configuration

The tests use the MongoDB configuration from `config.py` but append `_test` to the database name to avoid affecting production data.

If you need to use a different MongoDB instance for testing, you can set the `MONGO_URI` environment variable before running the tests:

```bash
# Example - setting a different MongoDB URI for testing
export MONGO_URI="mongodb://username:password@testhost:27017/test_db?authSource=admin"
python -m pytest
``` 