## ADDED Requirements

### Requirement: Unified object storage interface
The system SHALL provide a storage-agnostic interface for saving, reading, deleting, and addressing arbitrary files.

#### Scenario: Interface defines core operations
- **WHEN** a developer uses the object storage abstraction
- **THEN** the interface exposes `save`, `get`, `delete`, `get_url`, and `list` operations

### Requirement: Group-based object isolation
The system SHALL support organizing objects into groups similar to cloud storage buckets or prefixes.

#### Scenario: Save a file into a specific group
- **WHEN** a file is saved with a `group` parameter
- **THEN** the file is stored under the specified group path and the metadata records the group

#### Scenario: Save a file without a group
- **WHEN** a file is saved without a `group` parameter
- **THEN** the system uses a default group and stores the file accordingly

#### Scenario: List objects in a group
- **WHEN** the list method is called with a `group` parameter
- **THEN** the system returns only the objects belonging to that group

### Requirement: Local file system adapter
The system SHALL implement a local file system adapter that stores files under a configurable base path, defaulting to `.storage/` in the project root.

#### Scenario: Save a file locally
- **WHEN** a file is saved through the local adapter
- **THEN** the file is written to the configured storage path and metadata including key, filename, content type, size, group, and URL is returned

#### Scenario: Retrieve a saved file
- **WHEN** a file key is passed to the local adapter's get method
- **THEN** the system returns a readable binary stream of the stored file

#### Scenario: Delete a saved file
- **WHEN** a file key is passed to the local adapter's delete method
- **THEN** the file is removed from the storage path

#### Scenario: Generate file URL
- **WHEN** a file key is passed to the local adapter's get_url method
- **THEN** the system returns a URL composed of the configured base URL, group, and key

### Requirement: Storage adapter factory
The system SHALL provide a factory function that instantiates the appropriate adapter based on configuration.

#### Scenario: Factory returns local adapter by default
- **WHEN** the factory is called without explicit object storage configuration
- **THEN** the system returns a `LocalObjectStorage` instance

#### Scenario: Factory supports future object storage adapter
- **WHEN** the factory is configured for a supported object storage backend in the future
- **THEN** the system returns the corresponding adapter without changing business code

### Requirement: Stored object metadata model
The system SHALL define a metadata model that describes a stored file.

#### Scenario: Metadata contains required fields
- **WHEN** a file is saved
- **THEN** the returned metadata contains `key`, `filename`, `content_type`, `size`, `group`, `url`, and `created_at`

### Requirement: Unique storage keys
The system SHALL generate unique storage keys to avoid filename collisions.

#### Scenario: Save two files with the same filename
- **WHEN** two files with identical original filenames are saved
- **THEN** they receive distinct storage keys and both files are preserved

#### Scenario: Save two files with the same filename in different groups
- **WHEN** two files with identical original filenames are saved into different groups
- **THEN** they receive distinct storage keys and both files are preserved
