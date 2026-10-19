## ADDED Requirements

### Requirement: HTTP client settings

The system SHALL read the HTTP client TLS/proxy settings from the `http_ca_bundle`, `http_proxy`, `https_proxy` and `no_proxy` keys in the settings file. The settings values SHALL be the source of truth for these options, and TLS verification SHALL remain enabled.

#### Scenario: Missing keys use defaults

- **WHEN** the settings file does not contain the HTTP client keys
- **THEN** the effective values SHALL be empty strings
- **AND** the HTTP client SHALL use its default CA bundle and no explicit proxy

#### Scenario: Custom CA bundle is applied

- **WHEN** `http_ca_bundle` contains a valid path
- **THEN** the HTTP client SHALL use that file as the CA bundle

#### Scenario: HTTP proxies are applied

- **WHEN** `http_proxy` or `https_proxy` contain valid proxy URLs
- **THEN** the HTTP client SHALL use them for the corresponding schemes

#### Scenario: no_proxy bypasses configured proxies

- **WHEN** the requested host matches an entry in `no_proxy`
- **THEN** the HTTP client SHALL bypass the configured proxies for that request

#### Scenario: Invalid values fall back to defaults

- **WHEN** an HTTP client setting has an invalid type or an invalid proxy/path value
- **THEN** the system SHALL use the default value for that setting

#### Scenario: Environment variables do not override settings

- **WHEN** the settings values are present
- **THEN** the HTTP client SHALL use the settings values instead of proxy/CA environment variables

#### Scenario: TLS verification cannot be disabled

- **WHEN** the settings are loaded
- **THEN** TLS certificate verification SHALL remain enabled
- **AND** no settings key SHALL disable verification in this change
