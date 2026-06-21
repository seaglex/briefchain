## 1. Project Setup

- [x] 1.1 Create `src/briefchain/storage/` package structure
- [x] 1.2 Verify `pydantic` is available in dependencies

## 2. Core Abstraction

- [x] 2.1 Define `ObjectStorage` abstract interface in `src/briefchain/storage/base.py`
- [x] 2.2 Define `StoredObject` Pydantic metadata model in `src/briefchain/storage/base.py`
- [x] 2.3 Implement unique key generation helper
- [x] 2.4 Add `group` parameter to interface methods for bucket-like isolation

## 3. Local File System Adapter

- [x] 3.1 Implement `LocalObjectStorage` class in `src/briefchain/storage/local.py`
- [x] 3.2 Implement `save` method with binary stream or bytes input and optional group
- [x] 3.3 Implement `get` method returning a readable binary stream with optional group
- [x] 3.4 Implement `delete` method removing the stored file with optional group
- [x] 3.5 Implement `get_url` method returning base URL + group + key
- [x] 3.6 Implement `list` method returning objects in a given group
- [x] 3.7 Validate group names to prevent path traversal

## 4. Factory and Configuration

- [x] 4.1 Implement adapter factory in `src/briefchain/storage/factory.py`
- [x] 4.2 Read storage type and path from environment variables with defaults (`local` and project root `.storage/`)
- [x] 4.3 Export public API from `src/briefchain/storage/__init__.py`

## 5. Testing

- [x] 5.1 Add pytest fixture creating a temporary storage directory
- [x] 5.2 Write test for saving a file and verifying returned metadata
- [x] 5.3 Write test for retrieving saved file content
- [x] 5.4 Write test for deleting a saved file
- [x] 5.5 Write test for generating file URL
- [x] 5.6 Write test that two files with the same original name receive distinct keys
- [x] 5.7 Write test for saving files into different groups and verifying isolation
- [x] 5.8 Write test for listing objects within a group
- [x] 5.9 Write test for factory returning local adapter by default

## 6. Quality & Verification

- [x] 6.1 Run `ruff check` and `ruff format` on `src/briefchain/storage/` and `tests/`
- [x] 6.2 Verify all imports resolve with `python -c "from briefchain.storage import ObjectStorage, LocalObjectStorage"`
- [x] 6.3 Run full test suite and ensure all tests pass
