# Note on Architecture Diagrams

The architecture diagrams referenced in the documentation are defined as PlantUML source files in the `docs/diagrams/` directory.

To properly view these diagrams:

1. Use one of these methods to generate PNG files from the PlantUML sources:
   - Use an IDE plugin that supports PlantUML rendering (VS Code, IntelliJ, etc.)
   - Use the online PlantUML server: http://www.plantuml.com/plantuml/
   - Install the PlantUML CLI tool: `brew install plantuml` (macOS) or download from https://plantuml.com/download

2. For the marketecture diagram specifically:
   - Open `docs/diagrams/iotsphere_marketecture.puml` in a PlantUML-compatible editor
   - Or paste its contents into the online PlantUML editor: http://www.plantuml.com/plantuml/uml/

Following our Clean Architecture principles, the marketecture diagram illustrates:
- Core Business Entities at the center (capability-based device models)
- Business Logic surrounding the core (Device Shadow Service, etc.)
- Interface Adapters bridging business logic and external systems
- UI/Presentation Layer on the outside (API Gateway, WebSockets)
- Dependencies pointing inward to maintain architectural integrity
