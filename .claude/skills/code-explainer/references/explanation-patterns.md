# Code Explanation Patterns

This document provides proven patterns for explaining code effectively with clear structure and Mermaid diagrams.

## Table of Contents

1. [Function/Method Explanation Pattern](#functionmethod-explanation-pattern)
2. [Class/Component Explanation Pattern](#classcomponent-explanation-pattern)
3. [Architecture Overview Pattern](#architecture-overview-pattern)
4. [Data Flow Pattern](#data-flow-pattern)
5. [Algorithm Explanation Pattern](#algorithm-explanation-pattern)

---

## Function/Method Explanation Pattern

### Structure

```markdown
## [Function Name]

### Purpose
[One-sentence description of what the function does]

### Signature
\`\`\`[language]
[function signature]
\`\`\`

### Parameters
- **param1** ([type]): [description]
- **param2** ([type]): [description]

### Returns
- **[type]**: [description]

### Flow Diagram
\`\`\`mermaid
flowchart TD
    Start([Start]) --> Input[Receive Parameters]
    Input --> Process[Core Logic]
    Process --> Return[Return Result]
    Return --> End([End])
\`\`\`

### Logic Breakdown
1. **Step 1**: [Description]
   - [Detail]
   - [Detail]

2. **Step 2**: [Description]
   - [Detail]

### Key Points
- [Important consideration 1]
- [Important consideration 2]

### Example Usage
\`\`\`[language]
[example code]
\`\`\`

### Edge Cases
- [Edge case 1 and how it's handled]
- [Edge case 2 and how it's handled]
```

---

## Class/Component Explanation Pattern

### Structure

```markdown
## [Class Name]

### Purpose
[What problem this class solves]

### Class Diagram
\`\`\`mermaid
classDiagram
    class ClassName {
        -privateField: type
        +publicField: type
        +method1(params): returnType
        +method2(params): returnType
    }

    ClassName --> DependencyClass
\`\`\`

### Responsibilities
1. [Primary responsibility]
2. [Secondary responsibility]
3. [Tertiary responsibility]

### Key Properties
- **property1** ([type]): [description]
- **property2** ([type]): [description]

### Key Methods

#### method1(params)
- **Purpose**: [Brief description]
- **Returns**: [Return type and description]

#### method2(params)
- **Purpose**: [Brief description]
- **Returns**: [Return type and description]

### Dependencies
- **[Dependency 1]**: [Why it's needed]
- **[Dependency 2]**: [Why it's needed]

### Usage Pattern
\`\`\`[language]
[example instantiation and usage]
\`\`\`

### Lifecycle (if applicable)
\`\`\`mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Initialized
    Initialized --> Active
    Active --> Disposed
    Disposed --> [*]
\`\`\`
```

---

## Architecture Overview Pattern

### Structure

```markdown
## [System/Module Name] Architecture

### Overview
[High-level description of the system]

### Architecture Diagram
\`\`\`mermaid
graph TB
    subgraph "Presentation Layer"
        UI[UI Components]
    end

    subgraph "Business Layer"
        BL[Business Logic]
        SVC[Services]
    end

    subgraph "Data Layer"
        DB[(Database)]
        API[External APIs]
    end

    UI --> BL
    BL --> SVC
    SVC --> DB
    SVC --> API
\`\`\`

### Components

#### [Component 1 Name]
- **Role**: [Description]
- **Key Files**: [file1.py], [file2.py]
- **Interactions**: Communicates with [other components]

#### [Component 2 Name]
- **Role**: [Description]
- **Key Files**: [file1.py], [file2.py]
- **Interactions**: Communicates with [other components]

### Component Relationships
\`\`\`mermaid
graph LR
    A[Component A] -->|uses| B[Component B]
    B -->|depends on| C[Component C]
    A -->|configures| C
\`\`\`

### Directory Structure
\`\`\`
project/
├── component1/
│   ├── file1.py
│   └── file2.py
├── component2/
│   └── file.py
└── config/
    └── settings.py
\`\`\`

### Design Decisions
1. **[Decision 1]**: [Rationale]
2. **[Decision 2]**: [Rationale]

### Entry Points
- **[Entry Point 1]**: [Description and location]
- **[Entry Point 2]**: [Description and location]
```

---

## Data Flow Pattern

### Structure

```markdown
## [Feature Name] Data Flow

### Overview
[Description of what data flows through the system]

### Sequence Diagram
\`\`\`mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Service
    participant Database

    User->>Frontend: Action
    Frontend->>API: Request
    API->>Service: Process
    Service->>Database: Query
    Database-->>Service: Result
    Service-->>API: Response
    API-->>Frontend: Data
    Frontend-->>User: Display
\`\`\`

### Data Transformation Flow
\`\`\`mermaid
flowchart LR
    Input[Raw Input] --> Validate[Validation]
    Validate --> Transform[Transformation]
    Transform --> Process[Processing]
    Process --> Store[Storage]
    Store --> Output[Output]
\`\`\`

### Step-by-Step Breakdown

#### Step 1: [Stage Name]
- **Input**: [Description]
- **Process**: [What happens]
- **Output**: [Result]
- **Location**: [file.py:123]

#### Step 2: [Stage Name]
- **Input**: [Description]
- **Process**: [What happens]
- **Output**: [Result]
- **Location**: [file.py:456]

### Data Structures

#### Input Format
\`\`\`[language]
[example data structure]
\`\`\`

#### Output Format
\`\`\`[language]
[example data structure]
\`\`\`

### Error Handling
- **[Error Type 1]**: [How it's handled]
- **[Error Type 2]**: [How it's handled]
```

---

## Algorithm Explanation Pattern

### Structure

```markdown
## [Algorithm Name]

### Purpose
[What problem this algorithm solves]

### Algorithm Overview
[High-level description of the approach]

### Visual Representation
\`\`\`mermaid
flowchart TD
    Start([Start]) --> Check{Condition?}
    Check -->|Yes| ProcessA[Process A]
    Check -->|No| ProcessB[Process B]
    ProcessA --> Merge[Combine Results]
    ProcessB --> Merge
    Merge --> End([End])
\`\`\`

### Pseudocode
\`\`\`
function algorithmName(input):
    1. Initialize variables
    2. For each item in input:
        a. Check condition
        b. Process accordingly
    3. Return result
\`\`\`

### Complexity Analysis
- **Time Complexity**: O(n) - [Explanation]
- **Space Complexity**: O(1) - [Explanation]

### Step-by-Step Example

#### Input
\`\`\`
[example input]
\`\`\`

#### Execution Trace
1. **Step 1**: [State after step 1]
2. **Step 2**: [State after step 2]
3. **Step 3**: [State after step 3]

#### Output
\`\`\`
[example output]
\`\`\`

### Implementation
\`\`\`[language]
[actual code implementation]
\`\`\`

### Key Insights
- [Insight 1]
- [Insight 2]

### Trade-offs
- **Advantages**: [List]
- **Disadvantages**: [List]
- **Alternatives**: [Other approaches]
```

---

## General Guidelines

### Diagram Best Practices

1. **Keep diagrams focused**: One concept per diagram
2. **Use consistent styling**: Maintain visual consistency
3. **Add clear labels**: Every node and edge should be labeled
4. **Show direction**: Use arrows to indicate flow/dependency direction
5. **Group related elements**: Use subgraphs for logical grouping

### Writing Style

1. **Start with "why"**: Explain purpose before diving into details
2. **Use active voice**: "The function processes data" not "Data is processed"
3. **Be concise**: One sentence for simple concepts, paragraphs for complex ones
4. **Include examples**: Show concrete usage examples
5. **Link references**: Reference file:line locations for code elements

### Structure Principles

1. **Progressive disclosure**: Overview → Details → Examples
2. **Consistent formatting**: Use the same pattern throughout
3. **Visual hierarchy**: Use headings and formatting to guide readers
4. **Cross-references**: Link related sections and components
5. **Update regularly**: Keep explanations in sync with code changes
