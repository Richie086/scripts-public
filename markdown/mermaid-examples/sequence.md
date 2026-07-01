# Mermaid JS Sequence Diagram Example

Open this file in VS Code and use a Mermaid preview extension to see the rendered graph.
This sequence diagram illustrates a simple OAuth authentication flow.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant App
    participant AuthServer
    participant ResourceServer

    User->>App: Clicks Login
    App->>AuthServer: Request Authorization
    AuthServer-->>User: Prompt for Credentials
    User->>AuthServer: Submits Credentials
    AuthServer-->>App: Returns Auth Code
    App->>AuthServer: Exchange Code for Token
    AuthServer-->>App: Returns Access Token
    App->>ResourceServer: Request Data with Token
    ResourceServer-->>App: Return User Data
    App-->>User: Display Dashboard
```
